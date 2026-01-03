from __future__ import annotations

from tortoise import fields

from .base import BaseModel, TimestampMixin


class DailyRewardClaim(BaseModel, TimestampMixin):
    """One claim per user per server day."""

    user_id = fields.IntField(index=True, description="用户ID")
    claim_date = fields.DateField(index=True, description="领取日期(按服务器时区)")

    tier = fields.CharField(max_length=16, description="领取时会员等级")
    reward_amount = fields.BigIntField(description="实际发放奖励(已截断)")

    wallet_before = fields.BigIntField(description="发放前钱包余额")
    wallet_after = fields.BigIntField(description="发放后钱包余额")

    class Meta:
        table = "daily_reward_claim"
        unique_together = (("user_id", "claim_date"),)
