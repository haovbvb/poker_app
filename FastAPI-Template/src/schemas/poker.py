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
        default=15, ge=5, le=120, description="Action timeout"
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
    # NOTE: For the new A-mode quick-start UX, client does not need to pass any chip amount.
    # The server will use the user's wallet balance as the buy-in and lobby matching basis.
    # This field is kept for backward compatibility.
    max_chips: int | None = Field(
        default=None,
        ge=1,
        description="(可选) 玩家最大筹码/最大可买入；不传则使用钱包余额",
    )

    # Dev/testing helpers (all optional)
    auto_buyin: int | None = Field(
        default=None,
        ge=1,
        description="自动买入金额(可选)。若不传，将使用钱包余额。",
    )
    auto_seat: bool = Field(default=False, description="是否自动坐下(可选)")
    fill_bots: int = Field(default=0, ge=0, le=8, description="自动补机器人数量(可选)")
    bot_buyin: int | None = Field(
        default=None,
        ge=1,
        description="机器人买入金额(可选)。默认使用 auto_buyin/max_chips。",
    )


class PokerWSClientMessage(BaseModel):
    type: str
    last_seq: int | None = None
    hand_id: str | None = None
    action: str | None = None
    amount: int | None = None
    client_action_id: str | None = None
