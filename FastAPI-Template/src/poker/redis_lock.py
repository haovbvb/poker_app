from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass

import redis.asyncio as redis


_LOCK_RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
else
  return 0
end
"""


@dataclass(slots=True)
class RedisLock:
    redis: redis.Redis
    key: str
    ttl_ms: int = 2000

    async def acquire(self, *, timeout_ms: int = 5000) -> str:
        token = secrets.token_hex(16)
        deadline = asyncio.get_running_loop().time() + (timeout_ms / 1000)
        while True:
            ok = await self.redis.set(self.key, token, nx=True, px=self.ttl_ms)
            if ok:
                return token
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError(f"Failed to acquire lock: {self.key}")
            await asyncio.sleep(0.02)

    async def release(self, token: str) -> None:
        try:
            await self.redis.eval(_LOCK_RELEASE_LUA, 1, self.key, token)
        except Exception:
            # Best-effort; lock TTL protects against leaks.
            return
