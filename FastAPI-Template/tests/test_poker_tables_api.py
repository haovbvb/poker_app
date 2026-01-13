from httpx import AsyncClient


async def _set_wallet(async_client: AsyncClient, headers: dict, chips: int) -> None:
    me = await async_client.get("/api/v1/base/userinfo", headers=headers)
    assert me.status_code == 200
    user_id = me.json()["data"]["id"]

    from repositories.wallet import user_wallet_repository

    wallet = await user_wallet_repository.get_or_create(user_id=int(user_id))
    wallet.chips = int(chips)
    await wallet.save()


class TestPokerTablesAPI:
    async def test_create_list_join_buyin_seat_flow(
        self, async_client: AsyncClient, admin_token: str, normal_user_token: str
    ):
        headers = {"Authorization": f"Bearer {admin_token}"}
        headers2 = {"Authorization": f"Bearer {normal_user_token}"}

        # create
        r = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers,
            json={
                "name": "T1",
                "max_players": 6,
                "config": {"sb": 1, "bb": 2, "min_buyin": 40, "max_buyin": 200},
            },
        )
        assert r.status_code == 200
        table_id = r.json()["data"]["table_id"]
        assert isinstance(table_id, str) and table_id

        # list
        r = await async_client.get("/api/v1/poker/tables/list", headers=headers)
        assert r.status_code == 200
        tables = r.json()["data"]
        assert any(t["table_id"] == table_id for t in tables)

        # config
        r = await async_client.get(
            f"/api/v1/poker/tables/{table_id}/config", headers=headers
        )
        assert r.status_code == 200
        cfg = r.json()["data"]
        assert cfg["sb"] == 1
        assert cfg["bb"] == 2

        # snapshot
        r = await async_client.get(f"/api/v1/poker/tables/{table_id}", headers=headers)
        assert r.status_code == 200
        snap = r.json()["data"]
        assert snap["table"]["table_id"] == table_id
        assert "seats" in snap
        assert "members" in snap
        assert "hand" in snap

        # join/buyin/seat user1
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/join", headers=headers
        )
        assert r.status_code == 200

        await _set_wallet(async_client, headers, chips=1_000_000)

        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/buyin",
            headers=headers,
            json={"amount": 100},
        )
        assert r.status_code == 200

        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/seat",
            headers=headers,
            json={"seat_no": 1},
        )
        assert r.status_code == 200

        # join/buyin/seat user2 (second seat should trigger hand start)
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/join", headers=headers2
        )
        assert r.status_code == 200

        await _set_wallet(async_client, headers2, chips=1_000_000)

        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/buyin",
            headers=headers2,
            json={"amount": 100},
        )
        assert r.status_code == 200

        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/seat",
            headers=headers2,
            json={"seat_no": 2},
        )
        assert r.status_code == 200

        # events (HTTP replay)
        r = await async_client.get(
            f"/api/v1/poker/tables/{table_id}/events?since_seq=0", headers=headers
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert "events" in data
        assert isinstance(data["events"], list)

        events = data["events"]
        assert events, "events should not be empty after join/buyin/seat"
        types = [e.get("type") for e in events]
        assert "PLAYER_JOINED" in types
        assert "BUYIN_OK" in types
        assert "PLAYER_SEATED" in types
        assert "HAND_STARTED" in types
        assert "BLINDS_POSTED" in types
        assert "ACTION_REQUESTED" in types

        seqs = [int(e.get("seq")) for e in events if e.get("seq") is not None]
        assert seqs == sorted(seqs)
        assert len(seqs) == len(set(seqs))

        last_seq = seqs[-1]
        r = await async_client.get(
            f"/api/v1/poker/tables/{table_id}/events?since_seq={last_seq}",
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["events"] == []

    async def test_seat_requires_buyin(
        self, async_client: AsyncClient, admin_token: str
    ):
        headers = {"Authorization": f"Bearer {admin_token}"}

        r = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers,
            json={"name": "T2", "max_players": 6, "config": {}},
        )
        table_id = r.json()["data"]["table_id"]

        await async_client.post(
            f"/api/v1/poker/tables/{table_id}/join", headers=headers
        )

        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/seat",
            headers=headers,
            json={"seat_no": 1},
        )
        assert r.status_code == 400
        body = r.json()
        assert body.get("error_key") == "poker.buyin_required"

    async def test_buyin_out_of_range(
        self, async_client: AsyncClient, admin_token: str
    ):
        headers = {"Authorization": f"Bearer {admin_token}"}

        r = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers,
            json={
                "name": "T3",
                "max_players": 6,
                "config": {"min_buyin": 50, "max_buyin": 100},
            },
        )
        table_id = r.json()["data"]["table_id"]

        await async_client.post(
            f"/api/v1/poker/tables/{table_id}/join", headers=headers
        )

        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/buyin",
            headers=headers,
            json={"amount": 10},
        )
        assert r.status_code == 400
        body = r.json()
        assert body.get("error_key") == "poker.buyin_out_of_range"

    async def test_hand_start_deducts_fixed_consumption(
        self, async_client: AsyncClient, admin_token: str, normal_user_token: str, monkeypatch
    ):
        # 该用例只验证“每局固定消耗”扣费，不希望被自动补位机器人干扰座位与盲位。
        from settings import settings

        monkeypatch.setattr(settings, "POKER_BOTS_ENABLED", False, raising=False)

        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}

        # 设定一个易于断言的配置：ante 作为“每局固定消耗”。
        buyin = 100
        sb = 10
        bb = 20
        fee = 3

        r = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers_admin,
            json={
                "name": "FEE_T1",
                "max_players": 6,
                "config": {
                    "sb": sb,
                    "bb": bb,
                    "ante": fee,
                    "min_buyin": buyin,
                    "max_buyin": buyin,
                },
            },
        )
        assert r.status_code == 200
        table_id = r.json()["data"]["table_id"]

        # 两个玩家 join + buyin + 坐下；第二个玩家坐下会触发自动开局。
        await _set_wallet(async_client, headers_admin, chips=1_000_000)
        await _set_wallet(async_client, headers_user, chips=1_000_000)

        r = await async_client.post(f"/api/v1/poker/tables/{table_id}/join", headers=headers_admin)
        assert r.status_code == 200
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/buyin",
            headers=headers_admin,
            json={"amount": buyin},
        )
        assert r.status_code == 200
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/seat",
            headers=headers_admin,
            json={"seat_no": 1},
        )
        assert r.status_code == 200

        r = await async_client.post(f"/api/v1/poker/tables/{table_id}/join", headers=headers_user)
        assert r.status_code == 200
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/buyin",
            headers=headers_user,
            json={"amount": buyin},
        )
        assert r.status_code == 200
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/seat",
            headers=headers_user,
            json={"seat_no": 2},
        )
        assert r.status_code == 200

        snap = await async_client.get(f"/api/v1/poker/tables/{table_id}", headers=headers_admin)
        assert snap.status_code == 200
        data = snap.json()["data"]
        seats_list = data["seats"]
        seats_by_no = {str(s["seat_no"]): s for s in seats_list}
        hand = data.get("hand")
        assert hand is not None

        # 固定消耗 fee：从每个参与本手的玩家 stack 扣除，但不进底池。
        # 盲注扣款：以 hand.players[seat].committed 作为来源（避免假设按钮/盲注座位顺序）。
        for seat_no in ("1", "2"):
            committed = int(hand["players"][seat_no]["committed"])
            assert int(seats_by_no[seat_no]["stack"]) == int(buyin - fee - committed)

    async def test_quick_start_assigns_table_by_max_chips(
        self, async_client: AsyncClient, admin_token: str, normal_user_token: str
    ):
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}

        # PRD 2.1.2: max_chips 落在固定档位区间（例如 L2: 300K-1.5M，盲注 5K/10K）。
        # 创建两个相同档位的桌，quick_start 应优先选 seated 更少的。
        r1 = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers_admin,
            json={
                "name": "L2_A",
                "max_players": 6,
                "config": {"sb": 5000, "bb": 10000, "ante": 3000, "min_buyin": 300000, "max_buyin": 1500000},
            },
        )
        assert r1.status_code == 200
        t1 = r1.json()["data"]["table_id"]

        r2 = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers_admin,
            json={
                "name": "L2_B",
                "max_players": 6,
                "config": {"sb": 5000, "bb": 10000, "ante": 3000, "min_buyin": 300000, "max_buyin": 1500000},
            },
        )
        assert r2.status_code == 200
        t2 = r2.json()["data"]["table_id"]

        # 让 t1 有 1 个 seated（占用容量但仍可匹配），t2 保持空桌。
        r = await async_client.post(f"/api/v1/poker/tables/{t1}/join", headers=headers_admin)
        assert r.status_code == 200

        await _set_wallet(async_client, headers_admin, chips=10_000_000)
        r = await async_client.post(
            f"/api/v1/poker/tables/{t1}/buyin",
            headers=headers_admin,
            json={"amount": 300000},
        )
        assert r.status_code == 200
        r = await async_client.post(
            f"/api/v1/poker/tables/{t1}/seat",
            headers=headers_admin,
            json={"seat_no": 1},
        )
        assert r.status_code == 200

        r = await async_client.post(
            "/api/v1/poker/tables/quick_start",
            headers=headers_user,
            json={"max_chips": 900000},
        )
        assert r.status_code == 200
        chosen = r.json()["data"]["table_id"]
        assert chosen in {t1, t2}
        assert chosen == t2

    async def test_quick_start_creates_table_when_no_match(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}

        r = await async_client.post(
            "/api/v1/poker/tables/quick_start",
            headers=headers_user,
            json={"max_chips": 900000},
        )
        assert r.status_code == 200
        table_id = r.json()["data"]["table_id"]
        assert isinstance(table_id, str) and table_id

        # No existing table: should create PRD lobby level table (L2: 300K-1.5M, 5K/10K).
        cfg = await async_client.get(
            f"/api/v1/poker/tables/{table_id}/config", headers=headers_user
        )
        assert cfg.status_code == 200
        data = cfg.json()["data"]
        assert data["sb"] == 5000
        assert data["bb"] == 10000
        assert data["ante"] == 3000
        assert data["min_buyin"] == 300000
        assert data["max_buyin"] == 1500000

    async def test_lobby_levels_returns_default_levels(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}
        r = await async_client.get("/api/v1/poker/tables/lobby_levels", headers=headers_user)
        assert r.status_code == 200
        levels = r.json()["data"]
        assert isinstance(levels, list)
        assert len(levels) == 8
        required_keys = {"level", "min_buyin", "max_buyin", "sb", "bb", "ante", "is_vip"}
        assert required_keys.issubset(levels[0].keys())

    async def test_quick_start_out_of_range_returns_400(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}
        r = await async_client.post(
            "/api/v1/poker/tables/quick_start",
            headers=headers_user,
            json={"max_chips": 10},
        )
        assert r.status_code == 400
        body = r.json()
        assert body.get("error_key") == "poker.max_chips_out_of_range"

    async def test_vip_level_requires_pro_for_quick_start(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}
        # VIP 档位之一（例如 L5: 150M-750M）
        r = await async_client.post(
            "/api/v1/poker/tables/quick_start",
            headers=headers_user,
            # 需要同时满足：1) 在 VIP 档位区间内；2) 不触发钱包 cap
            json={"max_chips": 50_000_000},
        )
        assert r.status_code == 403
        body = r.json()
        assert body.get("error_key") == "subscription.tier_insufficient"

    async def test_vip_table_requires_pro_for_join_and_buyin(
        self, async_client: AsyncClient, admin_token: str, normal_user_token: str
    ):
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        headers_user = {"Authorization": f"Bearer {normal_user_token}"}

        # 创建一个 VIP 档位的桌（例如 L6: 150M-750M, 2.5M/5M，ante 1.5M）
        r = await async_client.post(
            "/api/v1/poker/tables/create",
            headers=headers_admin,
            json={
                "name": "VIP_L5",
                "max_players": 6,
                "config": {
                    "sb": 2_500_000,
                    "bb": 5_000_000,
                    "ante": 1_500_000,
                    "min_buyin": 150_000_000,
                    "max_buyin": 750_000_000,
                },
            },
        )
        assert r.status_code == 200
        table_id = r.json()["data"]["table_id"]

        # 普通用户 join 直接 403
        r = await async_client.post(f"/api/v1/poker/tables/{table_id}/join", headers=headers_user)
        assert r.status_code == 403
        assert r.json().get("error_key") == "subscription.tier_insufficient"

        # 普通用户 buyin 也 403（即使未 join）
        await _set_wallet(async_client, headers_user, chips=60_000_000)
        r = await async_client.post(
            f"/api/v1/poker/tables/{table_id}/buyin",
            headers=headers_user,
            json={"amount": 50_000_000},
        )
        assert r.status_code == 403
        assert r.json().get("error_key") == "subscription.tier_insufficient"
