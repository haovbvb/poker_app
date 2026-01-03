from __future__ import annotations

from datetime import date

from core.crud import CRUDBase
from models.rewards import DailyRewardClaim


class DailyRewardClaimRepository(CRUDBase[DailyRewardClaim, dict, dict]):
    def __init__(self):
        super().__init__(model=DailyRewardClaim)

    async def get_by_user_and_date(self, *, user_id: int, claim_date: date) -> DailyRewardClaim | None:
        return await self.model.filter(user_id=user_id, claim_date=claim_date).first()


daily_reward_claim_repository = DailyRewardClaimRepository()
