import json

from fastapi import APIRouter

from core.dependency import DependAuth
from repositories.wallet import user_wallet_repository
from schemas import Success
from services.subscription_tier import TIER_POLICY, get_user_effective_tier, tier_to_name

router = APIRouter()


@router.get("/me", summary="我的钱包", dependencies=[DependAuth])
async def my_wallet(user=DependAuth):
    wallet = await user_wallet_repository.get_or_create(user_id=user.id)
    tier_enum = await get_user_effective_tier(user_id=user.id)
    policy = TIER_POLICY[tier_enum]

    result = Success(
        data={
            "tier": tier_to_name(tier_enum),
            "wallet_cap": int(policy.wallet_chip_cap),
            "wallet_chips": int(wallet.chips),
        }
    )
    return json.loads(result.body)
