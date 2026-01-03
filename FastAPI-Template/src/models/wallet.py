from __future__ import annotations

from tortoise import fields

from .base import BaseModel, TimestampMixin


class UserWallet(BaseModel, TimestampMixin):
    """User wallet holding virtual chips (non-transferable)."""

    user_id = fields.IntField(unique=True, index=True, description="用户ID")
    chips = fields.BigIntField(default=0, description="钱包筹码余额")

    class Meta:
        table = "user_wallet"
