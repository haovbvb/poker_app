from __future__ import annotations

from core.crud import CRUDBase
from models.wallet import UserWallet


class UserWalletRepository(CRUDBase[UserWallet, dict, dict]):
    def __init__(self):
        super().__init__(model=UserWallet)

    async def get_by_user_id(self, user_id: int) -> UserWallet | None:
        return await self.model.filter(user_id=user_id).first()

    async def get_or_create(self, user_id: int) -> UserWallet:
        wallet = await self.get_by_user_id(user_id=user_id)
        if wallet:
            return wallet
        wallet = self.model(user_id=user_id, chips=0)
        await wallet.save()
        return wallet


user_wallet_repository = UserWalletRepository()
