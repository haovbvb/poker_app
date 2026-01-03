from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction

from core.exceptions import BusinessError
from repositories.wallet import user_wallet_repository
from repositories.welfare import bankruptcy_relief_claim_repository
from services.daily_rewards import next_reset_at, server_now, server_today
from services.subscription_tier import TIER_POLICY, get_user_effective_tier, tier_to_name
from settings import settings


@dataclass(frozen=True, slots=True)
class BankruptcyReliefStatus:
    server_date: date
    tier: str
    threshold_chips: int
    wallet_cap: int
    wallet_chips: int
    max_claims_per_day: int
    claimed_today: int
    remaining_today: int
    can_claim: bool
    consecutive_claim_days: int


@dataclass(frozen=True, slots=True)
class BankruptcyReliefClaimResult:
    server_date: date
    tier: str
    threshold_chips: int
    wallet_cap: int
    wallet_before: int
    wallet_after: int
    relief_awarded: int
    claimed_at: datetime
    client_request_id: str


def _threshold_chips() -> int:
    return int(getattr(settings, "BANKRUPTCY_THRESHOLD_CHIPS", 5_000_000))


def _max_claims_per_day() -> int:
    return int(getattr(settings, "BANKRUPTCY_MAX_CLAIMS_PER_DAY", 2))


def _prompt_subscribe_streak_days() -> int:
    return int(getattr(settings, "BANKRUPTCY_PROMPT_SUBSCRIBE_STREAK_DAYS", 3))


async def get_bankruptcy_relief_status(*, user_id: int) -> BankruptcyReliefStatus:
    today = server_today()

    tier_enum = await get_user_effective_tier(user_id=user_id)
    tier = tier_to_name(tier_enum)
    policy = TIER_POLICY[tier_enum]

    wallet = await user_wallet_repository.get_or_create(user_id=user_id)

    claimed_today = await bankruptcy_relief_claim_repository.count_by_user_and_date(
        user_id=user_id, claim_date=today
    )
    max_per_day = _max_claims_per_day()
    remaining = max(0, max_per_day - claimed_today)

    threshold = _threshold_chips()

    recent_dates = [today - timedelta(days=i) for i in range(_prompt_subscribe_streak_days())]
    claimed_dates = await bankruptcy_relief_claim_repository.list_claim_dates(
        user_id=user_id, claim_dates=recent_dates
    )

    streak = 0
    for d in recent_dates:
        if d in claimed_dates:
            streak += 1
        else:
            break

    can_claim = int(wallet.chips) < threshold and remaining > 0

    return BankruptcyReliefStatus(
        server_date=today,
        tier=tier,
        threshold_chips=threshold,
        wallet_cap=int(policy.wallet_chip_cap),
        wallet_chips=int(wallet.chips),
        max_claims_per_day=max_per_day,
        claimed_today=int(claimed_today),
        remaining_today=int(remaining),
        can_claim=can_claim,
        consecutive_claim_days=streak,
    )


async def claim_bankruptcy_relief(
    *, user_id: int, client_request_id: str
) -> BankruptcyReliefClaimResult:
    today = server_today()
    now = server_now()

    tier_enum = await get_user_effective_tier(user_id=user_id)
    tier = tier_to_name(tier_enum)
    policy = TIER_POLICY[tier_enum]

    threshold = _threshold_chips()
    max_per_day = _max_claims_per_day()

    async with in_transaction():
        wallet = await user_wallet_repository.get_or_create(user_id=user_id)

        existing = await bankruptcy_relief_claim_repository.get_by_user_and_client_request_id(
            user_id=user_id, client_request_id=client_request_id
        )
        if existing:
            return BankruptcyReliefClaimResult(
                server_date=existing.claim_date,
                tier=str(existing.tier),
                threshold_chips=int(existing.threshold_chips),
                wallet_cap=int(policy.wallet_chip_cap),
                wallet_before=int(existing.wallet_before),
                wallet_after=int(existing.wallet_after),
                relief_awarded=int(existing.relief_awarded),
                claimed_at=getattr(existing, "created_at"),
                client_request_id=str(existing.client_request_id),
            )

        wallet_before = int(wallet.chips)
        if wallet_before >= threshold:
            raise BusinessError(
                code=400,
                http_status=400,
                i18n_key="welfare.bankruptcy.not_eligible",
                params={"threshold": threshold},
            )

        claimed_today = await bankruptcy_relief_claim_repository.count_by_user_and_date(
            user_id=user_id, claim_date=today
        )
        if claimed_today >= max_per_day:
            raise BusinessError(
                code=400,
                http_status=400,
                i18n_key="welfare.bankruptcy.daily_limit_reached",
                params={"max": max_per_day},
            )

        cap = int(policy.wallet_chip_cap)
        wallet_after = min(threshold, cap)
        relief_awarded = max(0, wallet_after - wallet_before)

        if relief_awarded <= 0:
            # Extremely unlikely given cap >> threshold in current tiers.
            raise BusinessError(
                code=400,
                http_status=400,
                i18n_key="welfare.bankruptcy.not_eligible",
                params={"threshold": threshold},
            )

        wallet.chips = wallet_after
        await wallet.save()

        try:
            await bankruptcy_relief_claim_repository.create(
                {
                    "user_id": user_id,
                    "claim_date": today,
                    "client_request_id": client_request_id,
                    "tier": tier,
                    "threshold_chips": threshold,
                    "relief_awarded": relief_awarded,
                    "wallet_before": wallet_before,
                    "wallet_after": wallet_after,
                    "created_at": now,
                    "updated_at": now,
                }
            )
        except IntegrityError:
            dup = await bankruptcy_relief_claim_repository.get_by_user_and_client_request_id(
                user_id=user_id, client_request_id=client_request_id
            )
            if dup:
                return BankruptcyReliefClaimResult(
                    server_date=dup.claim_date,
                    tier=str(dup.tier),
                    threshold_chips=int(dup.threshold_chips),
                    wallet_cap=cap,
                    wallet_before=int(dup.wallet_before),
                    wallet_after=int(dup.wallet_after),
                    relief_awarded=int(dup.relief_awarded),
                    claimed_at=getattr(dup, "created_at"),
                    client_request_id=str(dup.client_request_id),
                )
            raise

    return BankruptcyReliefClaimResult(
        server_date=today,
        tier=tier,
        threshold_chips=threshold,
        wallet_cap=cap,
        wallet_before=wallet_before,
        wallet_after=wallet_after,
        relief_awarded=relief_awarded,
        claimed_at=now,
        client_request_id=client_request_id,
    )


__all__ = [
    "BankruptcyReliefStatus",
    "BankruptcyReliefClaimResult",
    "get_bankruptcy_relief_status",
    "claim_bankruptcy_relief",
    "next_reset_at",
]
