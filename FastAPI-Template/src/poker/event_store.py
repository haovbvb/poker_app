from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import redis.asyncio as redis


@dataclass(slots=True)
class EventStore:
    redis: redis.Redis | None = None
    maxlen: int = 1000
    _mem: dict[str, deque[dict[str, Any]]] = field(default_factory=dict, init=False)

    def _stream_key(self, table_id: str) -> str:
        return f"poker:table:{table_id}:events"

    def _ensure_mem(self, table_id: str) -> deque[dict[str, Any]]:
        if table_id not in self._mem:
            self._mem[table_id] = deque(maxlen=self.maxlen)
        return self._mem[table_id]

    async def append(self, table_id: str, *, seq: int, event: dict[str, Any]) -> str:
        """Append an event and return the stream id (or synthetic id in memory mode)."""
        if self.redis is None:
            self._ensure_mem(table_id).append(event)
            return f"{seq}-0"

        stream_id = f"{seq}-0"
        # Store a single JSON blob to avoid field explosion.
        await self.redis.xadd(
            self._stream_key(table_id),
            {"event": json.dumps(event, ensure_ascii=False)},
            id=stream_id,
            maxlen=self.maxlen,
            approximate=True,
        )
        return stream_id

    async def fetch_since(
        self, table_id: str, *, last_seq: int, limit: int = 200
    ) -> list[dict[str, Any]]:
        """Fetch events with seq > last_seq."""
        if self.redis is None:
            events = list(self._ensure_mem(table_id))
            out = [e for e in events if int(e.get("seq", 0)) > last_seq]
            return out[:limit]

        start = f"{last_seq + 1}-0"
        rows = await self.redis.xrange(
            self._stream_key(table_id), min=start, max="+", count=limit
        )
        out: list[dict[str, Any]] = []
        for _id, fields in rows:
            raw = fields.get("event")
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except Exception:
                continue
        return out

    async def get_latest_id(self, table_id: str) -> str:
        if self.redis is None:
            events = list(self._ensure_mem(table_id))
            if not events:
                return "0-0"
            return f"{int(events[-1].get('seq', 0))}-0"

        rows = await self.redis.xrevrange(
            self._stream_key(table_id), max="+", min="-", count=1
        )
        if not rows:
            return "0-0"
        return rows[0][0]

    async def read_blocking(
        self, table_id: str, *, last_id: str, block_ms: int = 5000, count: int = 100
    ) -> tuple[str, list[dict[str, Any]]]:
        """Blocking read for new events after last_id. Returns (new_last_id, events)."""
        if self.redis is None:
            # Memory mode can't block; return nothing.
            return last_id, []

        res = await self.redis.xread(
            {self._stream_key(table_id): last_id}, block=block_ms, count=count
        )
        if not res:
            return last_id, []

        # xread returns [(stream, [(id, {field:val}), ...])]
        _stream, entries = res[0]
        out: list[dict[str, Any]] = []
        new_last_id = last_id
        for entry_id, fields in entries:
            new_last_id = entry_id
            raw = fields.get("event")
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except Exception:
                continue
        return new_last_id, out
