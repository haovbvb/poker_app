from httpx import AsyncClient


class TestAdminWalletTopUpAPI:
    async def test_admin_wallet_topup_success(
        self, async_client: AsyncClient, admin_token: str, clean_database
    ):
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate
        from models.wallet import UserWallet

        user_in = UserCreate(
            username="topup_target_user",
            email="topup_target@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )
        user = await user_repository.create_user(obj_in=user_in)

        resp = await async_client.post(
            f"/api/v1/users/{user.id}/wallet/topup",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"amount": 12345, "note": "manual topup"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["user_id"] == user.id
        assert body["data"]["wallet_before"] == 0
        assert body["data"]["wallet_after"] == 12345
        assert body["data"]["amount"] == 12345

        wallet = await UserWallet.filter(user_id=user.id).first()
        assert wallet is not None
        assert int(wallet.chips) == 12345

    async def test_admin_wallet_topup_cap_exceeded(
        self, async_client: AsyncClient, admin_token: str, clean_database
    ):
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate

        user_in = UserCreate(
            username="topup_cap_user",
            email="topup_cap@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )
        user = await user_repository.create_user(obj_in=user_in)

        resp = await async_client.post(
            f"/api/v1/users/{user.id}/wallet/topup",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"amount": 100_000_001},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == 403
        assert body.get("error_key") == "subscription.wallet_cap_exceeded"

    async def test_admin_wallet_topup_invalid_amount(
        self, async_client: AsyncClient, admin_token: str, clean_database
    ):
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate

        user_in = UserCreate(
            username="topup_invalid_user",
            email="topup_invalid@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )
        user = await user_repository.create_user(obj_in=user_in)

        resp = await async_client.post(
            f"/api/v1/users/{user.id}/wallet/topup",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"amount": 0},
        )
        assert resp.status_code in (400, 422)
