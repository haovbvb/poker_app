from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from core.exceptions import BusinessError
from repositories.subscription import subscription_snapshot_repository
from settings.config import settings


class SubscriptionTier(IntEnum):
    NORMAL = 0
    PRO = 1
    GOLD = 2
    DIAMOND = 3
    SVIP = 4


_TIER_NAME: dict[SubscriptionTier, str] = {
    SubscriptionTier.NORMAL: "normal",
    SubscriptionTier.PRO: "pro",
    SubscriptionTier.GOLD: "gold",
    SubscriptionTier.DIAMOND: "diamond",
    SubscriptionTier.SVIP: "svip",
}


def tier_to_name(tier: SubscriptionTier) -> str:
    return _TIER_NAME.get(tier, "normal")


def tier_from_name(name: str | None) -> SubscriptionTier:
    raw = (name or "").strip().lower()
    if raw in {"svip"}:
        return SubscriptionTier.SVIP
    if raw in {"diamond"}:
        return SubscriptionTier.DIAMOND
    if raw in {"gold"}:
        return SubscriptionTier.GOLD
    if raw in {"pro"}:
        return SubscriptionTier.PRO
    return SubscriptionTier.NORMAL


def tier_from_product_id(product_id: str | None) -> SubscriptionTier | None:
    if not product_id:
        return None

    # 1) explicit mapping from env/config
    mapped = (settings.SUBSCRIPTION_PRODUCT_TIER_MAP or {}).get(product_id)
    if mapped:
        return tier_from_name(mapped)

    # 2) fallback heuristics
    pid = product_id.lower()
    if "svip" in pid:
        return SubscriptionTier.SVIP
    if "diamond" in pid:
        return SubscriptionTier.DIAMOND
    if "gold" in pid:
        return SubscriptionTier.GOLD
    if "pro" in pid:
        return SubscriptionTier.PRO

    return None


@dataclass(frozen=True, slots=True)
class TierPolicy:
    wallet_chip_cap: int
    daily_reward: int


TIER_POLICY: dict[SubscriptionTier, TierPolicy] = {
    SubscriptionTier.NORMAL: TierPolicy(wallet_chip_cap=100_000_000, daily_reward=10_000_000),
    SubscriptionTier.PRO: TierPolicy(wallet_chip_cap=200_000_000, daily_reward=50_000_000),
    SubscriptionTier.GOLD: TierPolicy(wallet_chip_cap=560_000_000, daily_reward=125_000_000),
    SubscriptionTier.DIAMOND: TierPolicy(wallet_chip_cap=1_550_000_000, daily_reward=310_000_000),
    SubscriptionTier.SVIP: TierPolicy(wallet_chip_cap=3_500_000_000, daily_reward=730_000_000),
}


# Poker table gating (template default: normal max_buyin=200)
DEFAULT_NORMAL_MAX_BUYIN: int = 200


async def get_user_effective_tier(user_id: int) -> SubscriptionTier:
    snaps = await subscription_snapshot_repository.list_by_user(user_id=user_id)

    best = SubscriptionTier.NORMAL
    for s in snaps:
        # Only active snapshots count.
        if getattr(s, "status", None) != "active":
            continue

        tier = tier_from_product_id(getattr(s, "product_id", None))
        if tier is None:
            continue

        if tier > best:
            best = tier

    return best


async def require_user_min_tier(
    *,
    user_id: int,
    required: SubscriptionTier,
    reason: str,
) -> SubscriptionTier:
    current = await get_user_effective_tier(user_id=user_id)
    if current < required:
        raise BusinessError(
            code=403,
            http_status=403,
            i18n_key="subscription.tier_insufficient",
            params={
                "required": tier_to_name(required),
                "current": tier_to_name(current),
                "reason": reason,
            },
        )
    return current


async def require_within_wallet_cap(*, user_id: int, requested_chips: int) -> SubscriptionTier:
    current = await get_user_effective_tier(user_id=user_id)
    cap = TIER_POLICY[current].wallet_chip_cap
    if requested_chips > cap:
        raise BusinessError(
            code=403,
            http_status=403,
            i18n_key="subscription.wallet_cap_exceeded",
            params={
                "cap": cap,
                "requested": requested_chips,
                "current": tier_to_name(current),
            },
        )
    return current
