from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class GrowthStatsWindowOut(BaseModel):
    total_hands: int = Field(description="总手牌")

    # MVP
    vpip: float = Field(description="VPIP(%)")
    pfr: float = Field(description="PFR(%)")
    af: Optional[float] = Field(description="AF(= (bet+raise)/call), 无 call 时为 null")
    three_bet: float = Field(description="3-bet(%)")
    wt: float = Field(description="WT(到摊牌率, %)")
    avg_win_per_hand: float = Field(description="平均每手赢取(按 pot collected 近似)")
    max_pot_win: int = Field(description="最大 POT 赢取")

    # Advanced
    win_rate: float = Field(description="胜率(%)")
    vpip_win_rate: Optional[float] = Field(description="入池胜率(入池后赢牌占比, %)")


class GrowthStatsOut(BaseModel):
    all: GrowthStatsWindowOut = Field(description="全量统计")
    last_30d: GrowthStatsWindowOut = Field(description="近30日统计")
