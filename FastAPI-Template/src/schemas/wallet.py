from __future__ import annotations

from pydantic import BaseModel, Field


class AdminWalletTopUpIn(BaseModel):
    amount: int = Field(..., ge=1, description="本次增加的筹码数量（累加到钱包余额）")
    note: str | None = Field(default=None, max_length=200, description="备注")


class AdminWalletTopUpOut(BaseModel):
    user_id: int = Field(..., description="被充值用户ID")
    operator_id: int = Field(..., description="操作人用户ID")
    amount: int = Field(..., description="本次实际增加的筹码")
    wallet_before: int = Field(..., description="充值前钱包余额")
    wallet_after: int = Field(..., description="充值后钱包余额")
    tier: str = Field(..., description="用户当前订阅等级")
    cap: int = Field(..., description="该订阅等级钱包筹码上限")
    note: str | None = Field(default=None, description="备注")
