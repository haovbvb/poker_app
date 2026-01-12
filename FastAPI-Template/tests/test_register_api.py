import uuid

import pytest


@pytest.mark.asyncio
async def test_register_returns_token_and_userinfo(async_client):
    uid = str(uuid.uuid4())[:8]
    payload = {
        "username": f"reg_{uid}",
        "email": f"reg_{uid}@test.com",
        "password": "Test123456",
    }

    r = await async_client.post("/api/v1/base/register", json=payload)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["username"] == payload["username"]
    assert data["token_type"] == "bearer"
    assert data.get("tier") in {"normal", "pro", "gold", "diamond", "svip"}

    me = await async_client.get(
        "/api/v1/base/userinfo",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    me_data = me.json()["data"]
    assert me_data["username"] == payload["username"]


@pytest.mark.asyncio
async def test_register_duplicate_username_rejected(async_client):
    uid = str(uuid.uuid4())[:8]
    payload = {
        "username": f"dup_{uid}",
        "email": f"dup_{uid}@test.com",
        "password": "Test123456",
    }

    r1 = await async_client.post("/api/v1/base/register", json=payload)
    assert r1.status_code == 200

    r2 = await async_client.post(
        "/api/v1/base/register",
        json={
            "username": payload["username"],
            "email": f"dup2_{uid}@test.com",
            "password": "Test123456",
        },
    )
    assert r2.status_code == 400
    body = r2.json()
    assert body.get("error_key") == "user.username_exists"


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(async_client):
    uid = str(uuid.uuid4())[:8]
    payload = {
        "username": f"dupe_{uid}",
        "email": f"dupe_{uid}@test.com",
        "password": "Test123456",
    }

    r1 = await async_client.post("/api/v1/base/register", json=payload)
    assert r1.status_code == 200

    r2 = await async_client.post(
        "/api/v1/base/register",
        json={
            "username": f"dupe2_{uid}",
            "email": payload["email"],
            "password": "Test123456",
        },
    )
    assert r2.status_code == 400
    body = r2.json()
    assert body.get("error_key") == "user.email_exists"
