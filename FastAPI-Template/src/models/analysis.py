from tortoise import fields
from models.base import BaseModel, TimestampMixin


class HandHistory(BaseModel, TimestampMixin):
    user_id = fields.BigIntField(index=True, description="Uploader User ID")
    platform = fields.CharField(
        max_length=50, null=True, description="Poker Platform (e.g. GG, PS)"
    )
    hand_id = fields.CharField(
        max_length=100, index=True, description="Platform Hand ID"
    )
    raw_content = fields.TextField(description="Raw Hand History Content")

    # Parsed metadata (can be expanded later)
    game_type = fields.CharField(
        max_length=50, null=True, description="Game Type (NLHE, PLO)"
    )
    stakes = fields.CharField(max_length=50, null=True, description="Stakes (e.g. 1/2)")
    hero_seat = fields.IntField(null=True, description="Hero Seat Number")
    hero_position = fields.CharField(
        max_length=10, null=True, description="Hero Position (BTN, SB, etc)"
    )

    # Derived per-hand stats (MVP growth metrics)
    hero_name = fields.CharField(max_length=64, null=True, description="Hero Name")
    parsed_ok = fields.BooleanField(default=False, description="Whether stats were parsed")

    vpip = fields.BooleanField(default=False, description="Voluntarily Put Money In Pot (preflop)")
    pfr = fields.BooleanField(default=False, description="Preflop Raise")
    three_bet = fields.BooleanField(default=False, description="3-bet (heuristic)")
    went_to_showdown = fields.BooleanField(default=False, description="Went To Showdown")
    won_hand = fields.BooleanField(default=False, description="Won the hand/pot")

    postflop_aggr_actions = fields.IntField(default=0, description="Postflop bets+raises")
    postflop_calls = fields.IntField(default=0, description="Postflop calls")
    won_amount = fields.BigIntField(default=0, description="Won amount (chips, heuristic)")

    # Analysis status
    is_analyzed = fields.BooleanField(default=False, description="Is Analyzed by AI")
    analysis_result = fields.JSONField(null=True, description="AI Analysis Result")

    class Meta:
        table = "hand_histories"
