from __future__ import annotations

from pydantic import BaseModel, Field


class PokerTableConfig(BaseModel):
    sb: int = Field(default=1, ge=1, description="Small blind")
    bb: int = Field(default=2, ge=1, description="Big blind")
    ante: int = Field(default=0, ge=0, description="Ante")
    straddle: bool = Field(default=False, description="Enable straddle")

    min_buyin: int = Field(default=40, ge=1, description="Minimum buy-in")
    max_buyin: int = Field(default=200, ge=1, description="Maximum buy-in")

    action_timeout_sec: int = Field(
        default=20, ge=5, le=120, description="Action timeout"
    )
    timebank_sec: int = Field(default=60, ge=0, le=600, description="Time bank")


class PokerTableCreateIn(BaseModel):
    name: str = Field(default="Texas Table", min_length=1, max_length=64)
    max_players: int = Field(default=9, ge=2, le=9)
    config: PokerTableConfig = Field(default_factory=PokerTableConfig)


class PokerTableInfo(BaseModel):
    table_id: str
    name: str
    max_players: int
    players_count: int
    seated_count: int
    created_at: float


class PokerJoinOut(BaseModel):
    table_id: str


class PokerBuyInIn(BaseModel):
    amount: int = Field(ge=1)


class PokerSeatIn(BaseModel):
    seat_no: int = Field(ge=1)


class PokerQuickStartIn(BaseModel):
    max_chips: int = Field(ge=1, description="玩家最大筹码/最大可买入")


class PokerWSClientMessage(BaseModel):
    type: str
    last_seq: int | None = None
    hand_id: str | None = None
    action: str | None = None
    amount: int | None = None
    client_action_id: str | None = None
