from datetime import datetime, timedelta

import pytest

from httpx import AsyncClient


class TestSubscriptionAPI:
    async def test_verify_ios_requires_original_transaction_id(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        r = await async_client.post(
            "/api/v1/subscriptions/verify",
            headers=headers,
            json={
                "platform": "ios",
                "product_id": "pro.monthly",
            },
        )
        assert r.status_code == 400
        body = r.json()
        # Real StoreKit2 verification expects signedTransactionInfo.
        assert body.get("error_key") in {
            "subscription.apple.missing_signed_transaction_info",
            "subscription.missing_original_transaction_id",
        }

    async def test_verify_android_requires_purchase_token(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        headers = {"Authorization": f"Bearer {normal_user_token}"}
        r = await async_client.post(
            "/api/v1/subscriptions/verify",
            headers=headers,
            json={
                "platform": "android",
                "product_id": "pro.monthly",
            },
        )
        assert r.status_code == 400
        body = r.json()
        assert body.get("error_key") == "subscription.missing_purchase_token"

    async def test_verify_and_list_me_idempotent(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        # Mock platform verifier so tests don't depend on external Apple/Google services.
        from models.enums import SubscriptionPlatform
        from services.billing.types import VerifiedSubscription
        import services.subscription_service as subsvc

        expected_expires_at = datetime.now() + timedelta(days=30)

        async def fake_verify_with_platform(body):
            return VerifiedSubscription(
                platform=SubscriptionPlatform.IOS,
                product_id=body.product_id,
                expires_at=expected_expires_at,
                auto_renew=True,
                environment="prod",
                ios_original_transaction_id="ot_123",
                ios_transaction_id="t_456",
                raw={"productId": body.product_id},
            )

        subsvc._verify_with_platform = fake_verify_with_platform  # type: ignore[attr-defined]

        headers = {"Authorization": f"Bearer {normal_user_token}"}
        expires_at = (datetime.now() + timedelta(days=1)).isoformat()

        payload = {
            "platform": "ios",
            "product_id": "pro.monthly",
            # signedTransactionInfo is required for real verification, but mocked here.
            "signed_transaction_info": "dummy.jws.payload",
            # The API should not trust client expires_at when verifier is wired.
            "expires_at": expires_at,
            "auto_renew": False,
        }

        r = await async_client.post(
            "/api/v1/subscriptions/verify", headers=headers, json=payload
        )
        assert r.status_code == 200
        body = r.json()["data"]
        assert body["idempotent"] is False
        snap = body["snapshot"]
        assert snap["platform"] == "ios"
        assert snap["product_id"] == "pro.monthly"
        assert snap["status"] in {"active", "inactive", "expired", "canceled"}
        assert snap["expires_at"] is not None

        # same request should be idempotent
        r2 = await async_client.post(
            "/api/v1/subscriptions/verify", headers=headers, json=payload
        )
        assert r2.status_code == 200
        body2 = r2.json()["data"]
        assert body2["idempotent"] is True

        # list my subscriptions
        r3 = await async_client.get("/api/v1/subscriptions/me", headers=headers)
        assert r3.status_code == 200
        items = r3.json()["data"]
        assert isinstance(items, list)
        assert any(
            i["product_id"] == "pro.monthly" and i["platform"] == "ios" for i in items
        )
