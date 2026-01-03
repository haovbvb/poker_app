from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction

from core.exceptions import BusinessError
from repositories.rewards import daily_reward_claim_repository
from repositories.wallet import user_wallet_repository
from services.subscription_tier import TIER_POLICY, get_user_effective_tier, tier_to_name
from settings import settings


@dataclass(frozen=True, slots=True)
class DailyRewardStatus:
    server_date: date
    tier: str
    base_reward: int
    wallet_cap: int
    wallet_chips: int
    can_claim: bool
    claimed_at: datetime | None


@dataclass(frozen=True, slots=True)
class DailyRewardClaimResult:
    server_date: date
    tier: str
    base_reward: int
    wallet_cap: int
    wallet_before: int
    wallet_after: int
    reward_awarded: int
    claimed_at: datetime


def _server_tz() -> ZoneInfo:
    tz_name = (settings.TORTOISE_ORM or {}).get("timezone") or "Asia/Shanghai"
    return ZoneInfo(tz_name)


def server_now() -> datetime:
    # store naive datetime for consistency with use_tz=False
    aware = datetime.now(tz=_server_tz())
    return aware.replace(tzinfo=None)


def server_today() -> date:
    return datetime.now(tz=_server_tz()).date()


def next_reset_at() -> datetime:
    tz = _server_tz()
    tomorrow = datetime.now(tz=tz).date() + timedelta(days=1)
    aware = datetime.combine(tomorrow, datetime.min.time(), tzinfo=tz)
    return aware.replace(tzinfo=None)


async def get_daily_reward_status(*, user_id: int) -> DailyRewardStatus:
    today = server_today()

    tier_enum = await get_user_effective_tier(user_id=user_id)
    tier = tier_to_name(tier_enum)

    policy = TIER_POLICY[tier_enum]
    wallet = await user_wallet_repository.get_or_create(user_id=user_id)

    claim = await daily_reward_claim_repository.get_by_user_and_date(
        user_id=user_id, claim_date=today
    )

    return DailyRewardStatus(
        server_date=today,
        tier=tier,
        base_reward=int(policy.daily_reward),
        wallet_cap=int(policy.wallet_chip_cap),
        wallet_chips=int(wallet.chips),
        can_claim=claim is None,
        claimed_at=getattr(claim, "created_at", None) if claim else None,
    )


async def claim_daily_reward(*, user_id: int) -> DailyRewardClaimResult:
    today = server_today()
    now = server_now()

    tier_enum = await get_user_effective_tier(user_id=user_id)
    tier = tier_to_name(tier_enum)
    policy = TIER_POLICY[tier_enum]

    async with in_transaction():
        wallet = await user_wallet_repository.get_or_create(user_id=user_id)

        existing = await daily_reward_claim_repository.get_by_user_and_date(
            user_id=user_id, claim_date=today
        )
        if existing:
            raise BusinessError(code=400, http_status=400, i18n_key="rewards.daily_already_claimed")

        wallet_before = int(wallet.chips)
        cap = int(policy.wallet_chip_cap)
        base_reward = int(policy.daily_reward)

        wallet_after = min(wallet_before + base_reward, cap)
        reward_awarded = max(0, wallet_after - wallet_before)

        wallet.chips = wallet_after
        await wallet.save()

        try:
            await daily_reward_claim_repository.create(
                {
                    "user_id": user_id,
                    "claim_date": today,
                    "tier": tier,
                    "reward_amount": reward_awarded,
                    "wallet_before": wallet_before,
                    "wallet_after": wallet_after,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except IntegrityError as exc:
            # Concurrency safety: unique (user_id, claim_date)
            raise BusinessError(code=400, http_status=400, i18n_key="rewards.daily_already_claimed") from exc

    return DailyRewardClaimResult(
        server_date=today,
        tier=tier,
        base_reward=base_reward,
        wallet_cap=cap,
        wallet_before=wallet_before,
        wallet_after=wallet_after,
        reward_awarded=reward_awarded,
        claimed_at=now,
    )
