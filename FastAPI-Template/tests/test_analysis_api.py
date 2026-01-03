import pytest
from httpx import AsyncClient


class TestAnalysisAPI:
    async def test_upload_hand_history(
        self, async_client: AsyncClient, normal_auth_headers
    ):
        payload = {
            "raw_content": "PokerStars Hand #22222222222: Tournament #11111111, $10+$1 USD Hold'em No Limit - Level I (10/20) - 2022/01/01 12:00:00 ET",
            "platform": "PokerStars",
        }
        response = await async_client.post(
            "/api/v1/hands/upload", json=payload, headers=normal_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["hand_id"] == "22222222222"
        assert data["data"]["platform"] == "PokerStars"
        assert data["data"]["is_analyzed"] is False

    async def test_list_hands(self, async_client: AsyncClient, normal_auth_headers):
        # Upload one first
        payload = {"raw_content": "Hand #TEST1234", "platform": "GGPoker"}
        await async_client.post(
            "/api/v1/hands/upload", json=payload, headers=normal_auth_headers
        )

        response = await async_client.get("/api/v1/hands", headers=normal_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["total"] >= 1
        assert len(data["data"]) >= 1
        assert data["data"][0]["hand_id"] == "TEST1234"
