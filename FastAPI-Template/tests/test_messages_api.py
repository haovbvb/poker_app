from httpx import AsyncClient


class TestMessagesAPI:
    async def test_message_flow_unread_read_delete(
        self, async_client: AsyncClient, admin_token: str, normal_user_token: str
    ):
        # admin create a message (RBAC-protected)
        create_resp = await async_client.post(
            "/api/v1/messages/create",
            json={
                "title": "系统公告",
                "content": "欢迎使用！",
                "type": "info",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_resp.status_code == 200

        # normal user cannot create
        create_resp2 = await async_client.post(
            "/api/v1/messages/create",
            json={
                "title": "should_fail",
                "content": "x",
                "type": "info",
            },
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert create_resp2.status_code in [401, 403]

        # list for user
        list_resp = await async_client.get(
            "/api/v1/messages/list",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert list_resp.status_code == 200
        body = list_resp.json()
        assert body["code"] == 200
        assert body["total"] >= 1
        first = body["data"][0]
        assert "id" in first
        assert first["is_read"] is False

        message_id = first["id"]

        # unread count
        unread_resp = await async_client.get(
            "/api/v1/messages/unread_count",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert unread_resp.status_code == 200
        unread = unread_resp.json()["data"]["unread_count"]
        assert unread >= 1

        # mark read
        read_resp = await async_client.post(
            f"/api/v1/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert read_resp.status_code == 200

        # unread count decreases
        unread_resp2 = await async_client.get(
            "/api/v1/messages/unread_count",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert unread_resp2.status_code == 200
        unread2 = unread_resp2.json()["data"]["unread_count"]
        assert unread2 == unread - 1

        # delete/hide message
        del_resp = await async_client.delete(
            f"/api/v1/messages/{message_id}",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert del_resp.status_code == 200

        list_resp2 = await async_client.get(
            "/api/v1/messages/list",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )
        assert list_resp2.status_code == 200
        ids = [row["id"] for row in list_resp2.json()["data"]]
        assert message_id not in ids
