import json

from fastapi import APIRouter, Header

from core.dependency import DependAuth
from core.exceptions import BusinessError
from repositories.subscription import subscription_snapshot_repository
from schemas import Success
from schemas.subscriptions import SubscriptionVerifyIn, SubscriptionWebhookIn
from services.subscription_service import verify_subscription, ingest_webhook
from settings.config import settings

router = APIRouter()


@router.post("/verify", summary="订阅验单与更新快照", dependencies=[DependAuth])
async def verify(body: SubscriptionVerifyIn, user=DependAuth):
    snapshot, idempotent = await verify_subscription(user_id=user.id, body=body)
    data = {
        "snapshot": await snapshot.to_dict(),
        "idempotent": idempotent,
    }
    result = Success(data=data)
    return json.loads(result.body)


@router.get("/me", summary="获取我的订阅快照", dependencies=[DependAuth])
async def my_subscriptions(user=DependAuth):
    snaps = await subscription_snapshot_repository.list_by_user(user_id=user.id)
    data = [await s.to_dict() for s in snaps]
    result = Success(data=data)
    return json.loads(result.body)


def _check_webhook_secret(x_webhook_secret: str | None):
    if not settings.SUBSCRIPTION_WEBHOOK_SECRET:
        return
    if not x_webhook_secret or x_webhook_secret != settings.SUBSCRIPTION_WEBHOOK_SECRET:
        raise BusinessError(
            code=401,
            i18n_key="subscription.webhook_unauthorized",
            http_status=401,
        )


@router.post("/webhooks/apple", summary="Apple 订阅回调入口")
async def apple_webhook(
    body: SubscriptionWebhookIn,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    _check_webhook_secret(x_webhook_secret)
    if body.platform != "ios":
        raise BusinessError(code=400, i18n_key="subscription.invalid_platform")

    snapshot, idempotent = await ingest_webhook(body)
    result = Success(
        data={
            "idempotent": idempotent,
            "snapshot": await snapshot.to_dict() if snapshot else None,
        }
    )
    return json.loads(result.body)


@router.post("/webhooks/google", summary="Google 订阅回调入口")
async def google_webhook(
    body: SubscriptionWebhookIn,
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
):
    _check_webhook_secret(x_webhook_secret)
    if body.platform != "android":
        raise BusinessError(code=400, i18n_key="subscription.invalid_platform")

    snapshot, idempotent = await ingest_webhook(body)
    result = Success(
        data={
            "idempotent": idempotent,
            "snapshot": await snapshot.to_dict() if snapshot else None,
        }
    )
    return json.loads(result.body)
