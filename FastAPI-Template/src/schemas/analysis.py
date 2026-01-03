from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class HandUploadIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "platform": "PokerStars",
                "raw_content": "PokerStars Hand #1234567890:  Hold'em No Limit ($0.05/$0.10 USD) - 2025/12/29 20:00:00 ET\n"
                "Table 'Alpha' 6-max Seat #1 is the button\n"
                "Seat 1: Hero ($10 in chips)\n"
                "Seat 2: Villain1 ($10 in chips)\n"
                "Seat 3: Villain2 ($10 in chips)\n"
                "Hero: posts small blind $0.05\n"
                "Villain1: posts big blind $0.10\n"
                "*** HOLE CARDS ***\n"
                "Dealt to Hero [As Kd]\n"
                "Villain2: folds\n"
                "Hero: raises $0.20 to $0.25\n"
                "Villain1: calls $0.15\n"
                "*** FLOP *** [Ah 7c 2d]\n"
                "Hero: bets $0.35\n"
                "Villain1: calls $0.35\n"
                "*** TURN *** [Ah 7c 2d] [9s]\n"
                "Hero: bets $0.90\n"
                "Villain1: folds\n"
                "Uncalled bet ($0.90) returned to Hero\n"
                "Hero collected $1.20 from pot\n"
                "*** SUMMARY ***\n"
                "Total pot $1.20 | Rake $0.00\n"
                "Seat 1: Hero collected ($1.20)\n"
            }
        }
    )
    raw_content: str = Field(..., description="Raw Hand History Text")
    platform: str | None = Field(None, description="Platform Name")


class HandHistoryOut(BaseModel):
    id: int
    hand_id: str
    platform: str | None
    game_type: str | None
    stakes: str | None
    created_at: datetime
    is_analyzed: bool

    class Config:
        from_attributes = True
