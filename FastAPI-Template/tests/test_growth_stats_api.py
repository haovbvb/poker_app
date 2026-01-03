from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest


@pytest.mark.asyncio
async def test_growth_stats_all_and_30d(async_client, normal_auth_headers):
    # Hand 1: VPIP+PFR+win
    hh1 = """
PokerStars Hand #H1:
*** HOLE CARDS ***
Dealt to Hero [As Ks]
Villain: calls 10
Hero: raises 30
Villain: calls 20
*** FLOP ***
Hero: bets 50
Villain: calls 50
*** TURN ***
Hero: calls 10
*** RIVER ***
Hero: bets 20
Villain: folds
Hero collected 110 from pot
*** SUMMARY ***
""".strip()

    # Hand 2: fold preflop
    hh2 = """
PokerStars Hand #H2:
*** HOLE CARDS ***
Dealt to Hero [2c 7d]
Villain: raises 10
Hero: folds
*** SUMMARY ***
""".strip()

    r1 = await async_client.post(
        "/api/v1/hands/upload", json={"raw_content": hh1, "platform": "PokerStars"}, headers=normal_auth_headers
    )
    assert r1.status_code == 200
    r2 = await async_client.post(
        "/api/v1/hands/upload", json={"raw_content": hh2, "platform": "PokerStars"}, headers=normal_auth_headers
    )
    assert r2.status_code == 200

    # Make hand2 older than 30 days
    me = await async_client.get("/api/v1/base/userinfo", headers=normal_auth_headers)
    assert me.status_code == 200
    user_id = me.json()["data"]["id"]

    from models.analysis import HandHistory

    tz = ZoneInfo("Asia/Shanghai")
    old_dt = datetime.now(tz) - timedelta(days=40)
    await HandHistory.filter(user_id=user_id, hand_id="H2").update(created_at=old_dt, updated_at=old_dt)

    stats_resp = await async_client.get("/api/v1/growth/stats", headers=normal_auth_headers)
    assert stats_resp.status_code == 200
    data = stats_resp.json()["data"]

    all_stats = data["all"]
    last_30d = data["last_30d"]

    assert all_stats["total_hands"] >= 2
    assert last_30d["total_hands"] >= 1

    # VPIP in all: only hh1 -> ~50%
    assert all_stats["vpip"] >= 49.0
    assert all_stats["vpip"] <= 51.0

    # VPIP in 30d: only hh1 -> 100%
    assert last_30d["vpip"] == 100.0

    # win rate in 30d: hh1 won -> 100%
    assert last_30d["win_rate"] == 100.0
