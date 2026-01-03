from __future__ import annotations

import itertools
from dataclasses import dataclass


_RANK_TO_INT = {r: i for i, r in enumerate("--23456789TJQKA")}


@dataclass(frozen=True, slots=True)
class HandRank:
    category: int
    tiebreak: tuple[int, ...]

    def as_tuple(self) -> tuple[int, tuple[int, ...]]:
        return self.category, self.tiebreak


def _parse_card(card: str) -> tuple[int, str]:
    if not isinstance(card, str) or len(card) != 2:
        raise ValueError(f"invalid card: {card!r}")
    r, s = card[0], card[1]
    if r not in _RANK_TO_INT or _RANK_TO_INT[r] == 0:
        raise ValueError(f"invalid rank: {card!r}")
    if s not in {"S", "H", "D", "C"}:
        raise ValueError(f"invalid suit: {card!r}")
    return _RANK_TO_INT[r], s


def _is_straight(ranks_desc: list[int]) -> int | None:
    # ranks_desc is unique and sorted desc.
    if len(ranks_desc) < 5:
        return None
    # Normal straight
    for i in range(len(ranks_desc) - 4):
        window = ranks_desc[i : i + 5]
        if window[0] - window[4] == 4 and len(set(window)) == 5:
            return window[0]
    # Wheel: A-5 straight
    if {14, 5, 4, 3, 2}.issubset(set(ranks_desc)):
        return 5
    return None


def rank_five(cards5: list[str]) -> HandRank:
    if len(cards5) != 5:
        raise ValueError("need 5 cards")

    parsed = [_parse_card(c) for c in cards5]
    ranks = [r for r, _s in parsed]
    suits = [_s for _r, _s in parsed]

    flush = len(set(suits)) == 1

    counts: dict[int, int] = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1

    ranks_unique_desc = sorted(counts.keys(), reverse=True)
    straight_high = _is_straight(sorted(set(ranks), reverse=True))

    # Build groups: sorted by (count desc, rank desc)
    groups = sorted(((cnt, r) for r, cnt in counts.items()), reverse=True)
    cnts = sorted(counts.values(), reverse=True)

    if straight_high is not None and flush:
        return HandRank(8, (straight_high,))

    if cnts == [4, 1]:
        quad_rank = groups[0][1]
        kicker = max(r for r in ranks_unique_desc if r != quad_rank)
        return HandRank(7, (quad_rank, kicker))

    if cnts == [3, 2]:
        trip = groups[0][1]
        pair = groups[1][1]
        return HandRank(6, (trip, pair))

    if flush:
        return HandRank(5, tuple(sorted(ranks, reverse=True)))

    if straight_high is not None:
        return HandRank(4, (straight_high,))

    if cnts == [3, 1, 1]:
        trip = groups[0][1]
        kickers = sorted((r for r in ranks_unique_desc if r != trip), reverse=True)
        return HandRank(3, (trip, *kickers))

    if cnts == [2, 2, 1]:
        pair1 = groups[0][1]
        pair2 = groups[1][1]
        hi, lo = max(pair1, pair2), min(pair1, pair2)
        kicker = max(r for r in ranks_unique_desc if r not in {pair1, pair2})
        return HandRank(2, (hi, lo, kicker))

    if cnts == [2, 1, 1, 1]:
        pair = groups[0][1]
        kickers = sorted((r for r in ranks_unique_desc if r != pair), reverse=True)
        return HandRank(1, (pair, *kickers))

    return HandRank(0, tuple(sorted(ranks, reverse=True)))


def rank_seven(cards7: list[str]) -> HandRank:
    if len(cards7) != 7:
        raise ValueError("need 7 cards")
    best: HandRank | None = None
    for combo in itertools.combinations(cards7, 5):
        r = rank_five(list(combo))
        if best is None or r.as_tuple() > best.as_tuple():
            best = r
    assert best is not None
    return best
