import json

from fastapi import APIRouter

from core.dependency import DependAuth
from schemas import Success
from services.daily_rewards import claim_daily_reward, get_daily_reward_status, next_reset_at

router = APIRouter()


@router.get("/daily", summary="每日奖励状态", dependencies=[DependAuth])
async def daily_status(user=DependAuth):
    status = await get_daily_reward_status(user_id=user.id)
    result = Success(
        data={
            "server_date": status.server_date.isoformat(),
            "tier": status.tier,
            "base_reward": status.base_reward,
            "wallet_cap": status.wallet_cap,
            "wallet_chips": status.wallet_chips,
            "can_claim": status.can_claim,
            "claimed_at": status.claimed_at.strftime("%Y-%m-%d %H:%M:%S") if status.claimed_at else None,
            "next_reset_at": next_reset_at().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return json.loads(result.body)


@router.post("/daily/claim", summary="领取每日奖励", dependencies=[DependAuth])
async def daily_claim(user=DependAuth):
    claimed = await claim_daily_reward(user_id=user.id)
    result = Success(
        data={
            "server_date": claimed.server_date.isoformat(),
            "tier": claimed.tier,
            "base_reward": claimed.base_reward,
            "wallet_cap": claimed.wallet_cap,
            "wallet_before": claimed.wallet_before,
            "wallet_after": claimed.wallet_after,
            "reward_awarded": claimed.reward_awarded,
            "claimed_at": claimed.claimed_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return json.loads(result.body)
