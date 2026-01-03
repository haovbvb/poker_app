from __future__ import annotations

from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import SubscriptionPlatform, SubscriptionStatus, SubscriptionSource


class SubscriptionFact(BaseModel, TimestampMixin):
    """Immutable subscription transaction facts.

    Each fact is an append-only record produced by verify/webhook/reconcile.
    The `dedupe_key` enforces idempotency at the persistence layer.
    """

    dedupe_key = fields.CharField(max_length=128, unique=True, index=True)

    platform = fields.CharEnumField(
        SubscriptionPlatform, description="平台", index=True
    )
    user_id = fields.IntField(null=True, description="用户ID", index=True)
    product_id = fields.CharField(max_length=128, description="商品ID", index=True)

    environment = fields.CharField(
        max_length=32, null=True, description="环境 sandbox/prod", index=True
    )

    ios_original_transaction_id = fields.CharField(
        max_length=128, null=True, description="iOS original_transaction_id", index=True
    )
    ios_transaction_id = fields.CharField(
        max_length=128, null=True, description="iOS transaction_id", index=True
    )

    android_purchase_token = fields.CharField(
        max_length=256, null=True, description="Android purchaseToken", index=True
    )
    android_order_id = fields.CharField(
        max_length=128, null=True, description="Android orderId", index=True
    )
    android_ack_state = fields.CharField(
        max_length=32, null=True, description="Android ack_state", index=True
    )

    status = fields.CharEnumField(
        SubscriptionStatus, null=True, description="事件对应订阅状态", index=True
    )
    expires_at = fields.DatetimeField(null=True, description="到期时间", index=True)
    event_time = fields.DatetimeField(null=True, description="事件时间", index=True)

    source = fields.CharEnumField(
        SubscriptionSource, description="事实来源", default=SubscriptionSource.VERIFY
    )

    raw_payload = fields.JSONField(null=True, description="原始负载(可选)")
    raw_payload_hash = fields.CharField(
        max_length=64, null=True, description="原始负载hash", index=True
    )

    class Meta:
        table = "subscription_fact"


class SubscriptionSnapshot(BaseModel, TimestampMixin):
    """Derived subscription state snapshot for fast reads."""

    user_id = fields.IntField(description="用户ID", index=True)
    platform = fields.CharEnumField(
        SubscriptionPlatform, description="平台", index=True
    )
    product_id = fields.CharField(max_length=128, description="商品ID", index=True)

    status = fields.CharEnumField(
        SubscriptionStatus, description="订阅状态", default=SubscriptionStatus.INACTIVE
    )
    expires_at = fields.DatetimeField(null=True, description="到期时间", index=True)
    auto_renew = fields.BooleanField(null=True, description="是否自动续订")
    last_event_at = fields.DatetimeField(
        null=True, description="最后事件时间", index=True
    )

    source = fields.CharEnumField(
        SubscriptionSource, description="快照来源", default=SubscriptionSource.VERIFY
    )

    ios_original_transaction_id = fields.CharField(
        max_length=128, null=True, description="iOS original_transaction_id", index=True
    )
    android_purchase_token = fields.CharField(
        max_length=256, null=True, description="Android purchaseToken", index=True
    )

    class Meta:
        table = "subscription_snapshot"
        unique_together = (("user_id", "platform", "product_id"),)
