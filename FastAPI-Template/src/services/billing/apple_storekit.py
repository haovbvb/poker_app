from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from core.exceptions import BusinessError


# NOTE: This is a public root certificate used to anchor Apple StoreKit JWS chains.
# If Apple rotates roots, update this value accordingly.
APPLE_ROOT_CA_G3_PEM = """-----BEGIN CERTIFICATE-----
MIICQzCCAcmgAwIBAgIILcX8iNLFS5UwCgYIKoZIzj0EAwMwZzEbMBkGA1UEAwwS
QXBwbGUgUm9vdCBDQSAtIEczMSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9u
IEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcN
MTQwNDMwMTgxOTA2WhcNMzkwNDMwMTgxOTA2WjBnMRswGQYDVQQDDBJBcHBsZSBS
b290IENBIC0gRzMxJjAkBgNVBAsMHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9y
aXR5MRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzB2MBAGByqGSM49
AgEGBSuBBAAiA2IABJjpLz1AcqTtkyJygRMc3RCV8cWjTnHcFBbZDuWmBSp3ZHtf
TjjTuxxEtX/1H7YyYl3J6YRbTzBPEVoA/VhYDKX1DyxNB0cTddqXl5dvMVztK517
IDvYuVTZXpmkOlEKMaNCMEAwHQYDVR0OBBYEFLuw3qFYM4iapIqZ3r6966/ayySr
MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMAoGCCqGSM49BAMDA2gA
MGUCMQCD6cHEFl4aXTQY2e3v9GwOAEZLuN+yRhHFD/3meoyhpmvOwgPUnPWTxnS4
at+qIxUCMG1mihDK1A3UT82NQz60imOlM27jbdoXt2QfyFMm+YhidDkLF1vLUagM
6BgD56KyKA==
-----END CERTIFICATE-----
"""


@dataclass(frozen=True)
class AppleTransaction:
    product_id: str
    bundle_id: str | None
    environment: str | None
    original_transaction_id: str | None
    transaction_id: str | None
    expires_at: datetime | None
    raw: dict[str, Any]


def _b64_to_der(cert_b64: str) -> bytes:
    return base64.b64decode(cert_b64)


def _load_x5c_chain(header: dict[str, Any]) -> list[x509.Certificate]:
    x5c = header.get("x5c")
    if not isinstance(x5c, list) or not x5c:
        raise BusinessError(code=400, i18n_key="subscription.apple.jws_missing_x5c")

    certs: list[x509.Certificate] = []
    for item in x5c:
        if not isinstance(item, str) or not item:
            raise BusinessError(code=400, i18n_key="subscription.apple.jws_invalid_x5c")
        certs.append(x509.load_der_x509_certificate(_b64_to_der(item)))
    return certs


def _verify_chain_to_root(chain: list[x509.Certificate], root_pem: str) -> None:
    # Minimal chain validation: verify each cert signature against the next cert public key.
    # Then ensure the chain anchors to the pinned Apple Root CA.
    root = x509.load_pem_x509_certificate(root_pem.encode("utf-8"))

    if not chain:
        raise BusinessError(code=400, i18n_key="subscription.apple.jws_invalid_x5c")

    def _get_validity(cert: x509.Certificate) -> tuple[datetime, datetime]:
        # cryptography exposes *_utc on newer versions
        not_before = getattr(cert, "not_valid_before_utc", cert.not_valid_before)
        not_after = getattr(cert, "not_valid_after_utc", cert.not_valid_after)
        # ensure naive datetime for comparisons
        return (
            not_before.replace(tzinfo=None),
            not_after.replace(tzinfo=None),
        )

    def _verify_cert_sig(child: x509.Certificate, parent: x509.Certificate) -> None:
        parent_key = parent.public_key()
        hash_alg = child.signature_hash_algorithm
        try:
            if isinstance(parent_key, rsa.RSAPublicKey):
                parent_key.verify(
                    child.signature,
                    child.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    hash_alg,
                )
            elif isinstance(parent_key, ec.EllipticCurvePublicKey):
                parent_key.verify(
                    child.signature,
                    child.tbs_certificate_bytes,
                    ec.ECDSA(hash_alg),
                )
            else:
                raise BusinessError(
                    code=400, i18n_key="subscription.apple.jws_invalid_key"
                )
        except BusinessError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise BusinessError(
                code=400, i18n_key="subscription.apple.jws_bad_chain"
            ) from exc

    # Validate time window
    now = datetime.utcnow().replace(tzinfo=None)
    for cert in chain:
        not_before, not_after = _get_validity(cert)
        if not_before > now or not_after < now:
            raise BusinessError(
                code=400, i18n_key="subscription.apple.jws_cert_expired"
            )

    # Verify signatures along the provided chain
    for idx in range(len(chain) - 1):
        child = chain[idx]
        parent = chain[idx + 1]
        if child.issuer != parent.subject:
            raise BusinessError(code=400, i18n_key="subscription.apple.jws_bad_chain")
        _verify_cert_sig(child, parent)

    # Anchor to pinned root.
    last = chain[-1]
    root_fp = root.fingerprint(hashes.SHA256())
    last_fp = last.fingerprint(hashes.SHA256())

    if last_fp == root_fp:
        return

    # If the root isn't included in x5c, verify the last cert is signed by the pinned root.
    if last.issuer != root.subject:
        raise BusinessError(code=400, i18n_key="subscription.apple.jws_untrusted_root")
    _verify_cert_sig(last, root)


def verify_and_parse_signed_transaction_info(
    signed_transaction_info: str,
) -> AppleTransaction:
    try:
        header = jwt.get_unverified_header(signed_transaction_info)
    except Exception as exc:  # noqa: BLE001
        raise BusinessError(
            code=400, i18n_key="subscription.apple.jws_invalid"
        ) from exc

    chain = _load_x5c_chain(header)
    _verify_chain_to_root(chain, APPLE_ROOT_CA_G3_PEM)

    leaf = chain[0]
    public_key = leaf.public_key()
    if not isinstance(public_key, EllipticCurvePublicKey):
        raise BusinessError(code=400, i18n_key="subscription.apple.jws_invalid_key")

    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    try:
        payload = jwt.decode(
            signed_transaction_info,
            key=pem_key,
            algorithms=["ES256"],
            options={
                "verify_aud": False,
                "verify_iss": False,
            },
        )
    except Exception as exc:  # noqa: BLE001
        raise BusinessError(
            code=400, i18n_key="subscription.apple.jws_verify_failed"
        ) from exc

    # StoreKit2 signedTransactionInfo is documented to include at least these fields.
    product_id = str(payload.get("productId") or "")
    if not product_id:
        raise BusinessError(code=400, i18n_key="subscription.apple.jws_missing_product")

    bundle_id = payload.get("bundleId")
    environment = payload.get("environment")
    original_transaction_id = payload.get("originalTransactionId")
    transaction_id = payload.get("transactionId")

    expires_at = None
    expires_ms = payload.get("expiresDate")
    if isinstance(expires_ms, (int, float)):
        expires_at = datetime.utcfromtimestamp(int(expires_ms) / 1000.0)

    return AppleTransaction(
        product_id=product_id,
        bundle_id=str(bundle_id) if bundle_id else None,
        environment=str(environment) if environment else None,
        original_transaction_id=(
            str(original_transaction_id) if original_transaction_id else None
        ),
        transaction_id=str(transaction_id) if transaction_id else None,
        expires_at=expires_at,
        raw=payload,
    )
