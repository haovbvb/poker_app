from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class DailyRewardStatusOut(BaseModel):
    server_date: date = Field(description="服务器日期(按服务器时区)")
    tier: str = Field(description="会员等级")
    base_reward: int = Field(description="基础奖励")
    wallet_cap: int = Field(description="钱包筹码上限")
    wallet_chips: int = Field(description="当前钱包余额")
    can_claim: bool = Field(description="今日是否可领取")
    claimed_at: Optional[str] = Field(default=None, description="今日领取时间")
    next_reset_at: str = Field(description="下次重置时间(服务器时区)")


class DailyRewardClaimOut(BaseModel):
    server_date: date = Field(description="服务器日期(按服务器时区)")
    tier: str = Field(description="会员等级")
    base_reward: int = Field(description="基础奖励")
    wallet_cap: int = Field(description="钱包筹码上限")
    wallet_before: int = Field(description="发放前钱包余额")
    wallet_after: int = Field(description="发放后钱包余额")
    reward_awarded: int = Field(description="实际发放(已截断)")
    claimed_at: str = Field(description="领取时间")
