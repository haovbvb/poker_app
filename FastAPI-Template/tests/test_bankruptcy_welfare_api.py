from __future__ import annotations

import uuid

import pytest

from repositories.wallet import user_wallet_repository


@pytest.mark.asyncio
async def test_bankruptcy_status_not_eligible(async_client, normal_user_token: str):
    headers = {"Authorization": f"Bearer {normal_user_token}"}

    # Default wallet is 0, so it should be eligible; set it above threshold to make it not eligible.
    me = await async_client.get("/api/v1/base/userinfo", headers=headers)
    assert me.status_code == 200
    user_id = me.json()["data"]["id"]

    wallet = await user_wallet_repository.get_or_create(user_id=user_id)
    wallet.chips = 6_000_000
    await wallet.save()

    resp = await async_client.get("/api/v1/welfare/bankruptcy/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["threshold_chips"] == 5_000_000
    assert data["wallet_chips"] == 6_000_000
    assert data["can_claim"] is False


@pytest.mark.asyncio
async def test_bankruptcy_claim_idempotent_and_limited(async_client, normal_user_token: str):
    headers = {"Authorization": f"Bearer {normal_user_token}"}

    me = await async_client.get("/api/v1/base/userinfo", headers=headers)
    assert me.status_code == 200
    user_id = me.json()["data"]["id"]

    # Make eligible
    wallet = await user_wallet_repository.get_or_create(user_id=user_id)
    wallet.chips = 1_000_000
    await wallet.save()

    status = await async_client.get("/api/v1/welfare/bankruptcy/status", headers=headers)
    assert status.status_code == 200
    sdata = status.json()["data"]
    assert sdata["can_claim"] is True
    assert sdata["remaining_today"] == 2

    rid = str(uuid.uuid4())
    claim1 = await async_client.post(
        "/api/v1/welfare/bankruptcy/claim",
        headers=headers,
        json={"client_request_id": rid},
    )
    assert claim1.status_code == 200
    c1 = claim1.json()["data"]
    assert c1["wallet_before"] == 1_000_000
    assert c1["wallet_after"] == 5_000_000
    assert c1["relief_awarded"] == 4_000_000

    # Idempotent retry with same request id
    claim1_retry = await async_client.post(
        "/api/v1/welfare/bankruptcy/claim",
        headers=headers,
        json={"client_request_id": rid},
    )
    assert claim1_retry.status_code == 200
    c1r = claim1_retry.json()["data"]
    assert c1r == c1

    # Make eligible again (simulate losing chips)
    wallet = await user_wallet_repository.get_or_create(user_id=user_id)
    wallet.chips = 2_000_000
    await wallet.save()

    rid2 = str(uuid.uuid4())
    claim2 = await async_client.post(
        "/api/v1/welfare/bankruptcy/claim",
        headers=headers,
        json={"client_request_id": rid2},
    )
    assert claim2.status_code == 200
    c2 = claim2.json()["data"]
    assert c2["wallet_before"] == 2_000_000
    assert c2["wallet_after"] == 5_000_000

    # Third claim in same day should hit daily limit (need to be eligible again)
    wallet = await user_wallet_repository.get_or_create(user_id=user_id)
    wallet.chips = 1_000_000
    await wallet.save()

    rid3 = str(uuid.uuid4())
    claim3 = await async_client.post(
        "/api/v1/welfare/bankruptcy/claim",
        headers=headers,
        json={"client_request_id": rid3},
    )
    assert claim3.status_code == 400
    payload = claim3.json()
    assert payload.get("error_key") == "welfare.bankruptcy.daily_limit_reached"
