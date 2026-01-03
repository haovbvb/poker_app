from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Iterable


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class DeterministicRng:
    """Deterministic RNG derived from a seed.

    Uses HMAC-SHA256(key=seed, msg=counter) blocks and provides unbiased randbelow
    via rejection sampling on uint32.

    This is stable across platforms and Python versions.
    """

    def __init__(self, seed: bytes):
        if not isinstance(seed, (bytes, bytearray)) or len(seed) == 0:
            raise ValueError("seed must be non-empty bytes")
        self._key = bytes(seed)
        self._counter = 0
        self._buf = b""

    def _next_block(self) -> bytes:
        self._counter += 1
        msg = self._counter.to_bytes(8, "big", signed=False)
        return hmac.new(self._key, msg, hashlib.sha256).digest()

    def _take(self, n: int) -> bytes:
        while len(self._buf) < n:
            self._buf += self._next_block()
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def randbelow(self, n: int) -> int:
        if n <= 0:
            raise ValueError("n must be positive")
        # Rejection sampling on 32-bit space.
        limit = (1 << 32) - ((1 << 32) % n)
        while True:
            x = int.from_bytes(self._take(4), "big", signed=False)
            if x < limit:
                return x % n


def build_standard_52_deck() -> list[str]:
    ranks = list("23456789TJQKA")
    suits = list("SHDC")
    return [r + s for r in ranks for s in suits]


def fisher_yates_shuffle(deck: list[str], rng: DeterministicRng) -> list[str]:
    d = list(deck)
    for i in range(len(d) - 1, 0, -1):
        j = rng.randbelow(i + 1)
        d[i], d[j] = d[j], d[i]
    return d


@dataclass(slots=True)
class DeckAudit:
    algo_version: str
    server_seed_hash: str
    deck_hash: str


@dataclass(slots=True)
class DeckManager:
    """Commit–reveal deck manager for a single hand."""

    table_id: str
    hand_id: str
    used_player_ids: list[int]

    algo_version: str = "fy-hmac-sha256-v1"
    server_seed: bytes | None = None
    server_seed_hash: str | None = None
    deck_hash: str | None = None

    _deck: list[str] | None = None
    _burned: list[str] | None = None

    def commit(self) -> DeckAudit:
        if self.server_seed is None:
            self.server_seed = secrets.token_bytes(32)
        self.server_seed_hash = _sha256_hex(self.server_seed)

        seed = self.derive_shuffle_seed(
            server_seed=self.server_seed,
            table_id=self.table_id,
            hand_id=self.hand_id,
            used_player_ids=self.used_player_ids,
        )
        rng = DeterministicRng(seed)
        deck = fisher_yates_shuffle(build_standard_52_deck(), rng)
        self._deck = deck
        self._burned = []
        self.deck_hash = _sha256_hex("|".join(deck).encode("utf-8"))
        return DeckAudit(
            algo_version=self.algo_version,
            server_seed_hash=self.server_seed_hash,
            deck_hash=self.deck_hash,
        )

    def reveal(self) -> str:
        if self.server_seed is None:
            raise RuntimeError("server_seed not initialized")
        return self.server_seed.hex()

    @staticmethod
    def derive_shuffle_seed(
        *,
        server_seed: bytes,
        table_id: str,
        hand_id: str,
        used_player_ids: Iterable[int],
    ) -> bytes:
        # Keep it explicit and versionable.
        pid_part = ",".join(str(int(x)) for x in sorted(used_player_ids)).encode(
            "utf-8"
        )
        material = (
            b"poker|deck|v1|"
            + server_seed
            + b"|"
            + table_id.encode("utf-8")
            + b"|"
            + hand_id.encode("utf-8")
            + b"|"
            + pid_part
        )
        return _sha256(material)

    def burn(self, n: int = 1) -> list[str]:
        if n <= 0:
            return []
        if not self._deck:
            raise RuntimeError("deck not committed")
        burned: list[str] = []
        for _ in range(n):
            if not self._deck:
                raise RuntimeError("deck exhausted")
            c = self._deck.pop()
            burned.append(c)
            assert self._burned is not None
            self._burned.append(c)
        return burned

    def deal(self, n: int = 1) -> list[str]:
        if n <= 0:
            return []
        if not self._deck:
            raise RuntimeError("deck not committed")
        out: list[str] = []
        for _ in range(n):
            if not self._deck:
                raise RuntimeError("deck exhausted")
            out.append(self._deck.pop())
        return out

    def remaining(self) -> int:
        return len(self._deck or [])

    def audit(self) -> DeckAudit:
        if self.server_seed_hash is None or self.deck_hash is None:
            raise RuntimeError("deck not committed")
        return DeckAudit(
            algo_version=self.algo_version,
            server_seed_hash=self.server_seed_hash,
            deck_hash=self.deck_hash,
        )
