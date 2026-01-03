from __future__ import annotations

from tortoise import fields

from .base import BaseModel, TimestampMixin


class BankruptcyReliefClaim(BaseModel, TimestampMixin):
    """Bankruptcy relief claim records.

    Idempotency is enforced by unique (user_id, client_request_id).
    Daily limits are enforced by counting records for claim_date.
    """

    user_id = fields.IntField(index=True, description="用户ID")
    claim_date = fields.DateField(index=True, description="领取日期(按服务器时区)")

    client_request_id = fields.CharField(
        max_length=64, index=True, description="客户端幂等请求ID(UUID)"
    )

    tier = fields.CharField(max_length=16, description="领取时会员等级")

    threshold_chips = fields.BigIntField(description="触发阈值")
    relief_awarded = fields.BigIntField(description="实际发放救济(已截断)")

    wallet_before = fields.BigIntField(description="发放前钱包余额")
    wallet_after = fields.BigIntField(description="发放后钱包余额")

    class Meta:
        table = "bankruptcy_relief_claim"
        unique_together = ("user_id", "client_request_id")
