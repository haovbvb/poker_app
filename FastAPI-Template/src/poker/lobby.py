from __future__ import annotations

from dataclasses import dataclass

from typing import Protocol


class TableConfigLike(Protocol):
    sb: int
    bb: int
    ante: int
    min_buyin: int
    max_buyin: int


@dataclass(frozen=True, slots=True)
class LobbyLevel:
    level: int
    min_buyin: int
    max_buyin: int
    sb: int
    bb: int
    ante: int
    is_vip: bool

    @property
    def name(self) -> str:
        return f"Lobby L{self.level} {self.min_buyin}-{self.max_buyin} ({self.sb}/{self.bb})"

    @property
    def config(self) -> "TableConfig":
        from poker.manager import TableConfig

        return TableConfig(
            sb=self.sb,
            bb=self.bb,
            ante=self.ante,
            min_buyin=self.min_buyin,
            max_buyin=self.max_buyin,
        )


# PRD 2.1.2: 按筹码区间分配桌（单位：chips，整数）
DEFAULT_LOBBY_LEVELS: list[LobbyLevel] = [
    LobbyLevel(level=1, min_buyin=150_000, max_buyin=750_000, sb=2_500, bb=5_000, ante=1_500, is_vip=False),
    LobbyLevel(level=2, min_buyin=300_000, max_buyin=1_500_000, sb=5_000, bb=10_000, ante=3_000, is_vip=False),
    LobbyLevel(level=3, min_buyin=1_500_000, max_buyin=7_500_000, sb=25_000, bb=50_000, ante=15_000, is_vip=False),
    LobbyLevel(level=4, min_buyin=6_000_000, max_buyin=30_000_000, sb=100_000, bb=200_000, ante=60_000, is_vip=False),
    LobbyLevel(level=5, min_buyin=30_000_000, max_buyin=150_000_000, sb=500_000, bb=1_000_000, ante=300_000, is_vip=True),
    LobbyLevel(level=6, min_buyin=150_000_000, max_buyin=750_000_000, sb=2_500_000, bb=5_000_000, ante=1_500_000, is_vip=True),
    LobbyLevel(level=7, min_buyin=600_000_000, max_buyin=3_000_000_000, sb=10_000_000, bb=20_000_000, ante=6_000_000, is_vip=True),
    LobbyLevel(level=8, min_buyin=3_000_000_000, max_buyin=15_000_000_000, sb=50_000_000, bb=100_000_000, ante=30_000_000, is_vip=True),
]


def find_lobby_level_for_max_chips(max_chips: int) -> LobbyLevel | None:
    best: LobbyLevel | None = None
    for lvl in DEFAULT_LOBBY_LEVELS:
        if lvl.min_buyin <= max_chips <= lvl.max_buyin:
            if best is None or lvl.min_buyin > best.min_buyin:
                best = lvl
    return best


def find_lobby_level_for_config(cfg: TableConfigLike) -> LobbyLevel | None:
    for lvl in DEFAULT_LOBBY_LEVELS:
        if (
            int(cfg.min_buyin) == lvl.min_buyin
            and int(cfg.max_buyin) == lvl.max_buyin
            and int(cfg.sb) == lvl.sb
            and int(cfg.bb) == lvl.bb
            and int(cfg.ante) == lvl.ante
        ):
            return lvl
    return None
