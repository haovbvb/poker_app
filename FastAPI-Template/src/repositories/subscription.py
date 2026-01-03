from __future__ import annotations

from datetime import datetime

from tortoise.expressions import Q

from core.crud import CRUDBase
from models.subscription import SubscriptionFact, SubscriptionSnapshot
from schemas.subscriptions import SubscriptionVerifyIn, SubscriptionWebhookIn


class SubscriptionFactRepository(CRUDBase[SubscriptionFact, dict, dict]):
    def __init__(self):
        super().__init__(model=SubscriptionFact)

    async def get_by_dedupe_key(self, dedupe_key: str) -> SubscriptionFact | None:
        return await self.model.filter(dedupe_key=dedupe_key).first()


class SubscriptionSnapshotRepository(CRUDBase[SubscriptionSnapshot, dict, dict]):
    def __init__(self):
        super().__init__(model=SubscriptionSnapshot)

    async def list_by_user(self, user_id: int) -> list[SubscriptionSnapshot]:
        return await self.model.filter(user_id=user_id).order_by("-updated_at").all()

    async def get_one(self, user_id: int, platform: str, product_id: str):
        return await self.model.filter(
            user_id=user_id, platform=platform, product_id=product_id
        ).first()


subscription_fact_repository = SubscriptionFactRepository()
subscription_snapshot_repository = SubscriptionSnapshotRepository()
