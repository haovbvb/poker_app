from __future__ import annotations

from datetime import date

from core.crud import CRUDBase
from models.welfare import BankruptcyReliefClaim


class BankruptcyReliefClaimRepository(CRUDBase[BankruptcyReliefClaim, dict, dict]):
    def __init__(self):
        super().__init__(model=BankruptcyReliefClaim)

    async def get_by_user_and_client_request_id(
        self, *, user_id: int, client_request_id: str
    ) -> BankruptcyReliefClaim | None:
        return await self.model.filter(
            user_id=user_id, client_request_id=client_request_id
        ).first()

    async def count_by_user_and_date(self, *, user_id: int, claim_date: date) -> int:
        return await self.model.filter(user_id=user_id, claim_date=claim_date).count()

    async def list_claim_dates(
        self, *, user_id: int, claim_dates: list[date]
    ) -> set[date]:
        rows = await self.model.filter(user_id=user_id, claim_date__in=claim_dates).values_list(
            "claim_date", flat=True
        )
        return set(rows)


bankruptcy_relief_claim_repository = BankruptcyReliefClaimRepository()
