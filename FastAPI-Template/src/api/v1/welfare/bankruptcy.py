import json

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.dependency import DependAuth
from schemas import Success
from services.bankruptcy_relief import (
    claim_bankruptcy_relief,
    get_bankruptcy_relief_status,
    next_reset_at,
)

router = APIRouter()


class BankruptcyClaimIn(BaseModel):
    client_request_id: str = Field(min_length=1, max_length=64, description="客户端幂等请求ID(UUID)")


@router.get("/bankruptcy/status", summary="破产救济状态", dependencies=[DependAuth])
async def bankruptcy_status(user=DependAuth):
    status = await get_bankruptcy_relief_status(user_id=user.id)
    result = Success(
        data={
            "server_date": status.server_date.isoformat(),
            "tier": status.tier,
            "threshold_chips": status.threshold_chips,
            "wallet_cap": status.wallet_cap,
            "wallet_chips": status.wallet_chips,
            "max_claims_per_day": status.max_claims_per_day,
            "claimed_today": status.claimed_today,
            "remaining_today": status.remaining_today,
            "can_claim": status.can_claim,
            "consecutive_claim_days": status.consecutive_claim_days,
            "should_prompt_subscribe": status.consecutive_claim_days >= 3,
            "next_reset_at": next_reset_at().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return json.loads(result.body)


@router.post("/bankruptcy/claim", summary="领取破产救济", dependencies=[DependAuth])
async def bankruptcy_claim(body: BankruptcyClaimIn, user=DependAuth):
    claimed = await claim_bankruptcy_relief(user_id=user.id, client_request_id=body.client_request_id)
    result = Success(
        data={
            "server_date": claimed.server_date.isoformat(),
            "tier": claimed.tier,
            "threshold_chips": claimed.threshold_chips,
            "wallet_cap": claimed.wallet_cap,
            "wallet_before": claimed.wallet_before,
            "wallet_after": claimed.wallet_after,
            "relief_awarded": claimed.relief_awarded,
            "client_request_id": claimed.client_request_id,
            "claimed_at": claimed.claimed_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return json.loads(result.body)
