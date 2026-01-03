from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.enums import SubscriptionPlatform


@dataclass(frozen=True)
class VerifiedSubscription:
    platform: SubscriptionPlatform
    product_id: str

    expires_at: datetime | None
    auto_renew: bool | None

    environment: str | None

    ios_original_transaction_id: str | None = None
    ios_transaction_id: str | None = None

    android_purchase_token: str | None = None
    android_order_id: str | None = None
    android_ack_state: str | None = None

    raw: dict[str, Any] | None = None
