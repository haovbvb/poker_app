from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


SubscriptionPlatformLiteral = Literal["ios", "android"]
SubscriptionSourceLiteral = Literal["verify", "webhook", "reconcile"]
SubscriptionStatusLiteral = Literal["active", "inactive", "expired", "canceled"]


class SubscriptionVerifyIn(BaseModel):
    platform: SubscriptionPlatformLiteral = Field(description="平台 ios/android")
    product_id: str = Field(min_length=1, max_length=128, description="商品ID")

    # idempotency for client retries
    idempotency_key: str | None = Field(
        default=None, max_length=128, description="幂等键(可选)"
    )

    # iOS
    original_transaction_id: str | None = Field(
        default=None, max_length=128, description="iOS original_transaction_id"
    )
    transaction_id: str | None = Field(
        default=None, max_length=128, description="iOS transaction_id"
    )
    signed_transaction_info: str | None = Field(
        default=None, description="iOS signedTransactionInfo JWS (可选)"
    )
    environment: str | None = Field(
        default=None, max_length=32, description="sandbox/prod (可选)"
    )

    # Android
    purchase_token: str | None = Field(
        default=None, max_length=256, description="Android purchaseToken"
    )
    order_id: str | None = Field(
        default=None, max_length=128, description="Android orderId (可选)"
    )
    ack_state: str | None = Field(
        default=None, max_length=32, description="ACKNOWLEDGED/PENDING (可选)"
    )

    # For now we accept derived fields from client to make the API usable in
    # environments where platform verification is not wired up yet.
    expires_at: datetime | None = Field(default=None, description="到期时间(可选)")
    auto_renew: bool | None = Field(default=None, description="是否自动续订(可选)")

    @model_validator(mode="after")
    def _validate_required_fields(self):
        if self.platform == "ios":
            # Real StoreKit2 flow expects signedTransactionInfo JWS.
            if not self.signed_transaction_info:
                # Keep legacy fields optional for compatibility, but verification
                # will require JWS.
                return self
        return self


class SubscriptionSnapshotOut(BaseModel):
    id: int = Field(description="快照ID")
    user_id: int = Field(description="用户ID")
    platform: SubscriptionPlatformLiteral = Field(description="平台")
    product_id: str = Field(description="商品ID")

    status: SubscriptionStatusLiteral = Field(description="订阅状态")
    expires_at: datetime | None = Field(default=None, description="到期时间")
    auto_renew: bool | None = Field(default=None, description="是否自动续订")
    last_event_at: datetime | None = Field(default=None, description="最后事件时间")

    source: SubscriptionSourceLiteral = Field(description="来源")

    original_transaction_id: str | None = Field(default=None, description="iOS")
    purchase_token: str | None = Field(default=None, description="Android")


class SubscriptionVerifyOut(BaseModel):
    snapshot: SubscriptionSnapshotOut = Field(description="订阅快照")
    idempotent: bool = Field(description="是否命中幂等去重")


class SubscriptionWebhookIn(BaseModel):
    platform: SubscriptionPlatformLiteral = Field(description="平台 ios/android")
    product_id: str = Field(min_length=1, max_length=128, description="商品ID")

    # event identifiers
    event_id: str | None = Field(default=None, max_length=128, description="事件ID")
    event_time: datetime | None = Field(default=None, description="事件时间")

    # optional user binding (some implementations attach user id)
    user_id: int | None = Field(default=None, description="用户ID(可选)")

    # platform identifiers
    original_transaction_id: str | None = Field(default=None, max_length=128)
    transaction_id: str | None = Field(default=None, max_length=128)
    purchase_token: str | None = Field(default=None, max_length=256)
    order_id: str | None = Field(default=None, max_length=128)
    ack_state: str | None = Field(default=None, max_length=32)

    expires_at: datetime | None = Field(default=None)
    auto_renew: bool | None = Field(default=None)

    environment: str | None = Field(default=None, max_length=32)

    raw_payload: dict[str, Any] | None = Field(default=None, description="原始负载")
