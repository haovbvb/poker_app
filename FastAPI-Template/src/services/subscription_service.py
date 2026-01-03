from __future__ import annotations

import hashlib
import json
from datetime import datetime

from core.exceptions import BusinessError
from models.enums import (
    SubscriptionPlatform,
    SubscriptionSource,
    SubscriptionStatus,
)
from models.subscription import SubscriptionSnapshot
from repositories.subscription import (
    subscription_fact_repository,
    subscription_snapshot_repository,
)
from schemas.subscriptions import (
    SubscriptionVerifyIn,
    SubscriptionWebhookIn,
)

from services.billing.apple_storekit import verify_and_parse_signed_transaction_info
from services.billing.google_play import fetch_subscription_from_google_play
from services.billing.types import VerifiedSubscription
from settings.config import settings


def _utcnow() -> datetime:
    # use naive datetime to match tortoise default config use_tz=False
    return datetime.now().replace(tzinfo=None)


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dedupe_key_from_verify(user_id: int, body: SubscriptionVerifyIn) -> str:
    if body.idempotency_key:
        base = (
            f"verify:{user_id}:{body.platform}:{body.product_id}:{body.idempotency_key}"
        )
        return _sha256_hex(base)

    if body.platform == "ios":
        # StoreKit2: prefer signedTransactionInfo (JWS) as idempotency input.
        if body.signed_transaction_info:
            base = (
                f"ios:jws:{_sha256_hex(body.signed_transaction_info)}:{body.product_id}"
            )
            return _sha256_hex(base)

        # Fallback: legacy/manual flow.
        if not body.original_transaction_id:
            raise BusinessError(
                code=400, i18n_key="subscription.missing_original_transaction_id"
            )
        base = f"ios:legacy:{body.original_transaction_id}:{body.transaction_id or ''}:{body.product_id}"
        return _sha256_hex(base)

    if body.platform == "android":
        if not body.purchase_token:
            raise BusinessError(
                code=400, i18n_key="subscription.missing_purchase_token"
            )
        base = f"android:{body.purchase_token}:{body.product_id}"
        return _sha256_hex(base)

    raise BusinessError(code=400, i18n_key="subscription.invalid_platform")


def _dedupe_key_from_webhook(body: SubscriptionWebhookIn) -> str:
    # Prefer explicit event id when available.
    if body.event_id:
        base = f"webhook:{body.platform}:{body.product_id}:{body.event_id}"
        return _sha256_hex(base)

    if body.platform == "ios" and body.original_transaction_id:
        base = f"webhook:ios:{body.product_id}:{body.original_transaction_id}:{body.transaction_id or ''}:{body.event_time or ''}"
        return _sha256_hex(base)

    if body.platform == "android" and body.purchase_token:
        base = f"webhook:android:{body.product_id}:{body.purchase_token}:{body.event_time or ''}"
        return _sha256_hex(base)

    # fallback: hash the raw payload-ish fields
    base = json.dumps(body.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    return _sha256_hex(f"webhook:fallback:{base}")


def _derive_status(expires_at: datetime | None) -> SubscriptionStatus:
    if not expires_at:
        return SubscriptionStatus.INACTIVE
    return (
        SubscriptionStatus.ACTIVE
        if expires_at > _utcnow()
        else SubscriptionStatus.EXPIRED
    )


async def _verify_with_platform(body: SubscriptionVerifyIn) -> VerifiedSubscription:
    if body.platform == "ios":
        if not body.signed_transaction_info:
            raise BusinessError(
                code=400, i18n_key="subscription.apple.missing_signed_transaction_info"
            )

        tx = verify_and_parse_signed_transaction_info(body.signed_transaction_info)

        if (
            settings.APPLE_BUNDLE_ID
            and tx.bundle_id
            and tx.bundle_id != settings.APPLE_BUNDLE_ID
        ):
            raise BusinessError(code=400, i18n_key="subscription.bundle_mismatch")

        if tx.product_id != body.product_id:
            raise BusinessError(code=400, i18n_key="subscription.product_mismatch")

        return VerifiedSubscription(
            platform=SubscriptionPlatform.IOS,
            product_id=tx.product_id,
            expires_at=tx.expires_at,
            auto_renew=None,
            environment=tx.environment,
            ios_original_transaction_id=tx.original_transaction_id,
            ios_transaction_id=tx.transaction_id,
            raw=tx.raw,
        )

    if body.platform == "android":
        if not body.purchase_token:
            raise BusinessError(
                code=400, i18n_key="subscription.missing_purchase_token"
            )

        gs = await fetch_subscription_from_google_play(
            service_account_json=settings.GOOGLE_PLAY_SERVICE_ACCOUNT_JSON,
            package_name=settings.GOOGLE_PLAY_PACKAGE_NAME,
            purchase_token=body.purchase_token,
            expected_product_id=body.product_id,
        )

        return VerifiedSubscription(
            platform=SubscriptionPlatform.ANDROID,
            product_id=gs.product_id,
            expires_at=gs.expires_at,
            auto_renew=gs.auto_renew,
            environment=None,
            android_purchase_token=gs.purchase_token,
            android_order_id=gs.order_id,
            android_ack_state=gs.ack_state,
            raw=gs.raw,
        )

    raise BusinessError(code=400, i18n_key="subscription.invalid_platform")


async def verify_subscription(
    user_id: int, body: SubscriptionVerifyIn
) -> tuple[SubscriptionSnapshot, bool]:
    dedupe_key = _dedupe_key_from_verify(user_id=user_id, body=body)

    existing_fact = await subscription_fact_repository.get_by_dedupe_key(dedupe_key)
    if existing_fact:
        snapshot = await subscription_snapshot_repository.get_one(
            user_id=user_id, platform=body.platform, product_id=body.product_id
        )
        if snapshot:
            return snapshot, True

    verified = await _verify_with_platform(body)
    status = _derive_status(verified.expires_at)
    now = _utcnow()

    raw_hash = None
    if body.signed_transaction_info:
        raw_hash = _sha256_hex(body.signed_transaction_info)
    elif body.purchase_token:
        raw_hash = _sha256_hex(body.purchase_token)

    await subscription_fact_repository.create(
        {
            "dedupe_key": dedupe_key,
            "platform": verified.platform,
            "user_id": user_id,
            "product_id": verified.product_id,
            "environment": verified.environment,
            "ios_original_transaction_id": verified.ios_original_transaction_id,
            "ios_transaction_id": verified.ios_transaction_id,
            "android_purchase_token": verified.android_purchase_token,
            "android_order_id": verified.android_order_id,
            "android_ack_state": verified.android_ack_state,
            "status": status,
            "expires_at": verified.expires_at,
            "event_time": now,
            "source": SubscriptionSource.VERIFY,
            "raw_payload": verified.raw or body.model_dump(mode="json"),
            "raw_payload_hash": raw_hash,
        }
    )

    snapshot = await subscription_snapshot_repository.get_one(
        user_id=user_id, platform=body.platform, product_id=body.product_id
    )

    data = {
        "user_id": user_id,
        "platform": verified.platform,
        "product_id": verified.product_id,
        "status": status,
        "expires_at": verified.expires_at,
        "auto_renew": verified.auto_renew,
        "last_event_at": now,
        "source": SubscriptionSource.VERIFY,
        "ios_original_transaction_id": verified.ios_original_transaction_id,
        "android_purchase_token": verified.android_purchase_token,
    }

    if snapshot:
        snapshot = snapshot.update_from_dict(data)
        await snapshot.save()
    else:
        snapshot = await subscription_snapshot_repository.create(data)

    return snapshot, False


async def ingest_webhook(
    body: SubscriptionWebhookIn,
) -> tuple[SubscriptionSnapshot | None, bool]:
    dedupe_key = _dedupe_key_from_webhook(body)

    existing_fact = await subscription_fact_repository.get_by_dedupe_key(dedupe_key)
    if existing_fact:
        if body.user_id:
            snapshot = await subscription_snapshot_repository.get_one(
                user_id=body.user_id, platform=body.platform, product_id=body.product_id
            )
            return snapshot, True
        return None, True

    status = _derive_status(body.expires_at)
    now = _utcnow()

    await subscription_fact_repository.create(
        {
            "dedupe_key": dedupe_key,
            "platform": SubscriptionPlatform(body.platform),
            "user_id": body.user_id,
            "product_id": body.product_id,
            "environment": body.environment,
            "ios_original_transaction_id": body.original_transaction_id,
            "ios_transaction_id": body.transaction_id,
            "android_purchase_token": body.purchase_token,
            "android_order_id": body.order_id,
            "android_ack_state": body.ack_state,
            "status": status,
            "expires_at": body.expires_at,
            "event_time": body.event_time or now,
            "source": SubscriptionSource.WEBHOOK,
            "raw_payload": body.raw_payload or body.model_dump(mode="json"),
            "raw_payload_hash": _sha256_hex(
                json.dumps(
                    body.model_dump(mode="json"), sort_keys=True, ensure_ascii=False
                )
            ),
        }
    )

    if not body.user_id:
        return None, False

    snapshot = await subscription_snapshot_repository.get_one(
        user_id=body.user_id, platform=body.platform, product_id=body.product_id
    )

    data = {
        "user_id": body.user_id,
        "platform": SubscriptionPlatform(body.platform),
        "product_id": body.product_id,
        "status": status,
        "expires_at": body.expires_at,
        "auto_renew": body.auto_renew,
        "last_event_at": body.event_time or now,
        "source": SubscriptionSource.WEBHOOK,
        "ios_original_transaction_id": body.original_transaction_id,
        "android_purchase_token": body.purchase_token,
    }

    if snapshot:
        snapshot = snapshot.update_from_dict(data)
        await snapshot.save()
    else:
        snapshot = await subscription_snapshot_repository.create(data)

    return snapshot, False
