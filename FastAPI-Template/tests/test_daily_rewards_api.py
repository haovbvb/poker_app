import pytest


@pytest.mark.asyncio
async def test_daily_reward_status_and_claim(async_client, normal_auth_headers):
    # initial status
    resp = await async_client.get("/api/v1/rewards/daily", headers=normal_auth_headers)
    assert resp.status_code == 200
    payload = resp.json()["data"]
    assert payload["can_claim"] is True
    assert payload["wallet_chips"] == 0
    assert payload["base_reward"] > 0

    # claim
    resp2 = await async_client.post(
        "/api/v1/rewards/daily/claim", headers=normal_auth_headers
    )
    assert resp2.status_code == 200
    claimed = resp2.json()["data"]
    assert claimed["reward_awarded"] == claimed["base_reward"]
    assert claimed["wallet_after"] == claimed["wallet_before"] + claimed["reward_awarded"]

    # status after claim
    resp3 = await async_client.get("/api/v1/rewards/daily", headers=normal_auth_headers)
    assert resp3.status_code == 200
    payload3 = resp3.json()["data"]
    assert payload3["can_claim"] is False


@pytest.mark.asyncio
async def test_daily_reward_double_claim_rejected(async_client, normal_auth_headers):
    resp = await async_client.post(
        "/api/v1/rewards/daily/claim", headers=normal_auth_headers
    )
    assert resp.status_code == 200

    resp2 = await async_client.post(
        "/api/v1/rewards/daily/claim", headers=normal_auth_headers
    )
    assert resp2.status_code == 400
    body = resp2.json()
    assert body.get("error_key") == "rewards.daily_already_claimed"


@pytest.mark.asyncio
async def test_daily_reward_wallet_cap_clamp(async_client, normal_auth_headers):
    # ensure wallet exists
    resp = await async_client.get("/api/v1/rewards/daily", headers=normal_auth_headers)
    assert resp.status_code == 200
    status = resp.json()["data"]

    # get user id
    me = await async_client.get("/api/v1/base/userinfo", headers=normal_auth_headers)
    assert me.status_code == 200
    user_id = me.json()["data"]["id"]

    cap = int(status["wallet_cap"])

    from models.wallet import UserWallet

    # set wallet to cap-1 so today's reward is heavily truncated
    await UserWallet.filter(user_id=user_id).update(chips=cap - 1)

    resp2 = await async_client.post(
        "/api/v1/rewards/daily/claim", headers=normal_auth_headers
    )
    assert resp2.status_code == 200
    claimed = resp2.json()["data"]

    assert claimed["wallet_after"] == cap
    assert claimed["reward_awarded"] == 1
