from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

from core.exceptions import BusinessError


ANDROID_PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher"


@dataclass(frozen=True)
class GoogleSubscription:
    product_id: str
    package_name: str
    purchase_token: str

    expires_at: datetime | None
    auto_renew: bool | None
    order_id: str | None
    ack_state: str | None

    raw: dict[str, Any]


def _parse_rfc3339(ts: str) -> datetime:
    # Google Play returns RFC3339 timestamps like 2025-01-01T00:00:00Z
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).replace(tzinfo=None)


async def fetch_subscription_from_google_play(
    service_account_json: str,
    package_name: str,
    purchase_token: str,
    expected_product_id: str,
    timeout_sec: float = 10.0,
) -> GoogleSubscription:
    if not service_account_json:
        raise BusinessError(code=500, i18n_key="subscription.google.config_missing")
    if not package_name:
        raise BusinessError(code=500, i18n_key="subscription.google.config_missing")

    try:
        info = json.loads(service_account_json)
    except Exception as exc:  # noqa: BLE001
        raise BusinessError(
            code=500, i18n_key="subscription.google.config_invalid"
        ) from exc

    creds = service_account.Credentials.from_service_account_info(
        info, scopes=[ANDROID_PUBLISHER_SCOPE]
    )
    creds.refresh(GoogleAuthRequest())
    if not creds.token:
        raise BusinessError(code=500, i18n_key="subscription.google.auth_failed")

    url = (
        "https://androidpublisher.googleapis.com/androidpublisher/v3/"
        f"applications/{package_name}/purchases/subscriptionsv2/tokens/{purchase_token}"
    )

    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {creds.token}"})

    if resp.status_code >= 400:
        raise BusinessError(
            code=400,
            i18n_key="subscription.google.verify_failed",
            params={"status": resp.status_code},
        )

    payload: dict[str, Any] = resp.json()

    # subscriptionsv2 response structure: lineItems[].productId, expiryTime
    line_items = payload.get("lineItems")
    if not isinstance(line_items, list) or not line_items:
        raise BusinessError(code=400, i18n_key="subscription.google.invalid_response")

    item = line_items[0]
    product_id = str(item.get("productId") or "")
    if not product_id:
        raise BusinessError(code=400, i18n_key="subscription.google.invalid_response")

    if product_id != expected_product_id:
        raise BusinessError(code=400, i18n_key="subscription.product_mismatch")

    expires_at = None
    expiry_time = item.get("expiryTime")
    if isinstance(expiry_time, str) and expiry_time:
        expires_at = _parse_rfc3339(expiry_time)

    # Order id can be in "latestOrderId" on top-level for some responses.
    order_id = payload.get("latestOrderId")
    if order_id is not None:
        order_id = str(order_id)

    # ack state in v2: "acknowledgementState"
    ack_state_val = payload.get("acknowledgementState")
    ack_state = str(ack_state_val) if ack_state_val is not None else None

    # auto renew info can be represented via subscriptionState or autoRenewEnabled
    auto_renew = None
    auto_renew_enabled = payload.get("autoRenewEnabled")
    if isinstance(auto_renew_enabled, bool):
        auto_renew = auto_renew_enabled

    return GoogleSubscription(
        product_id=product_id,
        package_name=package_name,
        purchase_token=purchase_token,
        expires_at=expires_at,
        auto_renew=auto_renew,
        order_id=order_id,
        ack_state=ack_state,
        raw=payload,
    )
