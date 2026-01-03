from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from models.analysis import HandHistory
from schemas.analysis import HandUploadIn
from settings.config import settings


@dataclass(frozen=True, slots=True)
class ParsedHandStats:
    hero_name: str | None
    parsed_ok: bool
    vpip: bool
    pfr: bool
    three_bet: bool
    went_to_showdown: bool
    won_hand: bool
    postflop_aggr_actions: int
    postflop_calls: int
    won_amount: int


_RE_ACTION = re.compile(r"^(?P<player>[^:]{1,64}):\s+(?P<action>folds|calls|checks|bets|raises|shows|mucks)(?P<rest>.*)$", re.IGNORECASE)


def _server_tz() -> ZoneInfo:
    tzname = "Asia/Shanghai"
    try:
        tzname = (settings.TORTOISE_ORM or {}).get("timezone") or tzname
    except Exception:
        tzname = "Asia/Shanghai"
    return ZoneInfo(tzname)


def _extract_section(raw: str, start_markers: list[str], end_markers: list[str]) -> str:
    lower = raw
    start_idx = -1
    for m in start_markers:
        i = lower.find(m)
        if i != -1:
            start_idx = i + len(m)
            break
    if start_idx == -1:
        return ""

    end_idx = len(raw)
    for m in end_markers:
        i = lower.find(m, start_idx)
        if i != -1:
            end_idx = min(end_idx, i)
    return raw[start_idx:end_idx]


def _guess_hero_name(raw: str) -> str | None:
    # PokerStars style: "Dealt to <name> [..]"
    m = re.search(r"Dealt to\s+([^\[]+?)\s*\[", raw)
    if m:
        return m.group(1).strip()

    # GG style sometimes uses "Dealt to Hero"
    if "Dealt to Hero" in raw:
        return "Hero"

    return None


def _parse_won_amount(raw: str, hero_name: str) -> int:
    # Heuristic: first/maximum "<hero> collected <amount>" occurrence.
    # Accept formats like "collected 440" or "collected $4.40".
    amounts: list[int] = []

    for m in re.finditer(rf"{re.escape(hero_name)}\s+collected\s+\$?(\d+(?:\.\d+)?)", raw, flags=re.IGNORECASE):
        try:
            amounts.append(int(round(float(m.group(1)))))
        except Exception:
            continue

    if not amounts:
        # Alternative wording
        for m in re.finditer(rf"{re.escape(hero_name)}\s+wins\s+\$?(\d+(?:\.\d+)?)", raw, flags=re.IGNORECASE):
            try:
                amounts.append(int(round(float(m.group(1)))))
            except Exception:
                continue

    return max(amounts) if amounts else 0


def parse_hand_history_stats(raw_content: str, *, hero_name: str | None = None) -> ParsedHandStats:
    hero = (hero_name or _guess_hero_name(raw_content) or "Hero").strip()

    # Preflop section
    preflop = _extract_section(
        raw_content,
        start_markers=["*** HOLE CARDS ***", "HOLE CARDS"],
        end_markers=["*** FLOP ***", "*** SUMMARY ***", "*** SHOW DOWN ***"],
    )

    vpip = False
    pfr = False
    three_bet = False
    raises_before_hero = 0

    if preflop:
        for line in preflop.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _RE_ACTION.match(line)
            if not m:
                continue
            player = m.group("player").strip()
            action = m.group("action").lower()

            if player != hero:
                if action == "raises":
                    raises_before_hero += 1
                continue

            # Hero action
            if action in {"calls", "raises", "bets"}:
                vpip = True
            if action == "raises":
                pfr = True
                if raises_before_hero >= 1:
                    three_bet = True

    # Postflop actions
    postflop = _extract_section(
        raw_content,
        start_markers=["*** FLOP ***", "*** TURN ***", "*** RIVER ***"],
        end_markers=["*** SUMMARY ***"],
    )

    postflop_aggr = 0
    postflop_calls = 0
    if postflop:
        for line in postflop.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _RE_ACTION.match(line)
            if not m:
                continue
            if m.group("player").strip() != hero:
                continue
            action = m.group("action").lower()
            if action in {"bets", "raises"}:
                postflop_aggr += 1
            elif action == "calls":
                postflop_calls += 1

    went_to_showdown = False
    if "*** SHOW DOWN ***" in raw_content:
        if re.search(rf"{re.escape(hero)}.*(shows|showed)", raw_content, flags=re.IGNORECASE):
            went_to_showdown = True

    won_hand = False
    if re.search(rf"{re.escape(hero)}\s+collected\b", raw_content, flags=re.IGNORECASE):
        won_hand = True
    elif re.search(rf"{re.escape(hero)}\s+wins\b", raw_content, flags=re.IGNORECASE):
        won_hand = True

    won_amount = _parse_won_amount(raw_content, hero)
    parsed_ok = bool(preflop or postflop)

    return ParsedHandStats(
        hero_name=hero,
        parsed_ok=parsed_ok,
        vpip=vpip,
        pfr=pfr,
        three_bet=three_bet,
        went_to_showdown=went_to_showdown,
        won_hand=won_hand,
        postflop_aggr_actions=postflop_aggr,
        postflop_calls=postflop_calls,
        won_amount=won_amount,
    )


async def upload_hand_history(user_id: int, data: HandUploadIn) -> HandHistory:
    # Simple heuristic to extract Hand ID if possible
    hand_id = "unknown"

    # Common patterns
    # PokerStars: "PokerStars Hand #1234567890:"
    # GGPoker: "Hand #1234567890"
    match = re.search(r"Hand #(\w+)", data.raw_content)
    if match:
        hand_id = match.group(1)

    parsed = parse_hand_history_stats(data.raw_content)

    # Create record
    hand = await HandHistory.create(
        user_id=user_id,
        raw_content=data.raw_content,
        platform=data.platform or "unknown",
        hand_id=hand_id,
        hero_name=parsed.hero_name,
        parsed_ok=parsed.parsed_ok,
        vpip=parsed.vpip,
        pfr=parsed.pfr,
        three_bet=parsed.three_bet,
        went_to_showdown=parsed.went_to_showdown,
        won_hand=parsed.won_hand,
        postflop_aggr_actions=parsed.postflop_aggr_actions,
        postflop_calls=parsed.postflop_calls,
        won_amount=parsed.won_amount,
    )
    return hand


def _pct(num: int, den: int) -> float:
    if den <= 0:
        return 0.0
    return round((num / den) * 100.0, 2)


async def _aggregate_growth_stats(*, user_id: int, since: datetime | None) -> dict[str, object]:
    q = HandHistory.filter(user_id=user_id)
    if since is not None:
        q = q.filter(created_at__gte=since)

    rows = await q.all()
    total = len(rows)

    vpip_h = sum(1 for r in rows if getattr(r, "vpip", False))
    pfr_h = sum(1 for r in rows if getattr(r, "pfr", False))
    three_h = sum(1 for r in rows if getattr(r, "three_bet", False))
    wt_h = sum(1 for r in rows if getattr(r, "went_to_showdown", False))
    win_h = sum(1 for r in rows if getattr(r, "won_hand", False))

    vpip_win_h = sum(1 for r in rows if getattr(r, "vpip", False) and getattr(r, "won_hand", False))
    total_won_amount = sum(int(getattr(r, "won_amount", 0) or 0) for r in rows)
    max_pot_win = max((int(getattr(r, "won_amount", 0) or 0) for r in rows), default=0)

    aggr = sum(int(getattr(r, "postflop_aggr_actions", 0) or 0) for r in rows)
    calls = sum(int(getattr(r, "postflop_calls", 0) or 0) for r in rows)
    af = round(aggr / calls, 2) if calls > 0 else None

    avg_win = round(total_won_amount / total, 2) if total > 0 else 0.0
    vpip_win_rate = round((vpip_win_h / vpip_h) * 100.0, 2) if vpip_h > 0 else None

    return {
        "total_hands": total,
        "vpip": _pct(vpip_h, total),
        "pfr": _pct(pfr_h, total),
        "af": af,
        "three_bet": _pct(three_h, total),
        "wt": _pct(wt_h, total),
        "avg_win_per_hand": avg_win,
        "max_pot_win": int(max_pot_win),
        "win_rate": _pct(win_h, total),
        "vpip_win_rate": vpip_win_rate,
    }


async def get_growth_stats(*, user_id: int) -> dict[str, dict[str, object]]:
    tz = _server_tz()
    now = datetime.now(tz)
    since_30d = now - timedelta(days=30)
    return {
        "all": await _aggregate_growth_stats(user_id=user_id, since=None),
        "last_30d": await _aggregate_growth_stats(user_id=user_id, since=since_30d),
    }


async def get_user_hands(
    user_id: int, limit: int = 20, offset: int = 0
) -> list[HandHistory]:
    return (
        await HandHistory.filter(user_id=user_id)
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
    )
