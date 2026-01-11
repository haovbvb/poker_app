import asyncio

import pytest

from poker import poker_manager
from poker.manager import TableConfig
from settings.config import settings


@pytest.mark.asyncio
async def test_bots_autofill_starts_hand_with_single_human(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "POKER_BOTS_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_TARGET_PLAYERS", 2, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_ACTION_DELAY_MS", 0, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_RAISE_PROB", 0.0, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_FOLD_PROB_FACING_BET", 0.0, raising=False)

    table = await poker_manager.create_table(
        name="T_bots_autofill_2p",
        max_players=6,
        config=TableConfig(sb=1, bb=2, min_buyin=1, max_buyin=1000, action_timeout_sec=5),
    )

    # Sit the only human at seat 2 so the auto-filled bot takes seat 1 and acts first.
    await table.ensure_member(user_id=100, username="u100")
    await table.buyin(user_id=100, amount=100)
    await table.sit(user_id=100, seat_no=2)

    # Give the bot task a moment to run.
    await asyncio.sleep(0.05)

    assert table.state.hand is not None
    assert len(table.state.hand.players) == 2
    assert any(seat.user_id < 0 for seat in table.state.seats.values())

    events = await table.fetch_events_since(0)
    assert any(
        e.get("type") == "ACTION_TAKEN" and int((e.get("payload") or {}).get("user_id") or 0) < 0
        for e in events
        if isinstance(e, dict)
    )


@pytest.mark.asyncio
async def test_bots_autofill_respects_target_players(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "POKER_BOTS_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_TARGET_PLAYERS", 4, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_ACTION_DELAY_MS", 0, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_RAISE_PROB", 0.0, raising=False)
    monkeypatch.setattr(settings, "POKER_BOTS_FOLD_PROB_FACING_BET", 0.0, raising=False)

    table = await poker_manager.create_table(
        name="T_bots_autofill_4p",
        max_players=6,
        config=TableConfig(sb=1, bb=2, min_buyin=1, max_buyin=1000, action_timeout_sec=5),
    )

    await table.ensure_member(user_id=200, username="u200")
    await table.buyin(user_id=200, amount=100)
    await table.sit(user_id=200, seat_no=2)

    await asyncio.sleep(0.05)

    assert table.state.hand is not None
    assert len(table.state.hand.players) == 4
    bot_seats = [s for s in table.state.seats.values() if s.user_id < 0]
    assert len(bot_seats) == 3
