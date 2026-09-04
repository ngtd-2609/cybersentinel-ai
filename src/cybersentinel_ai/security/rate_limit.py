from collections import defaultdict, deque
from dataclasses import dataclass
from hashlib import sha256
from time import monotonic

from redis.asyncio import Redis
from redis.exceptions import RedisError

LOGIN_RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('PTTL', KEYS[1])
return {current, ttl}
"""


class RateLimitUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int


class LoginRateLimiter:
    def __init__(self, redis_url: str | None, *, key_prefix: str = "login-rate"):
        self.redis = Redis.from_url(redis_url, decode_responses=True) if redis_url else None
        self.key_prefix = key_prefix
        self.local_attempts: dict[str, deque[float]] = defaultdict(deque)

    def _key(self, client_key: str) -> str:
        digest = sha256(client_key.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}:{digest}"

    async def consume(
        self,
        client_key: str,
        *,
        limit: int,
        window_seconds: int,
        fail_closed: bool,
    ) -> RateLimitDecision:
        if self.redis is not None:
            try:
                count, ttl_ms = await self.redis.eval(
                    LOGIN_RATE_LIMIT_SCRIPT,
                    1,
                    self._key(client_key),
                    window_seconds * 1000,
                )
                return RateLimitDecision(
                    allowed=int(count) <= limit,
                    retry_after=max(1, (int(ttl_ms) + 999) // 1000),
                )
            except (RedisError, OSError):
                if fail_closed:
                    raise RateLimitUnavailableError("Distributed rate limiter unavailable")
        return self._consume_local(client_key, limit=limit, window_seconds=window_seconds)

    def _consume_local(
        self, client_key: str, *, limit: int, window_seconds: int
    ) -> RateLimitDecision:
        now = monotonic()
        attempts = self.local_attempts[client_key]
        while attempts and now - attempts[0] >= window_seconds:
            attempts.popleft()
        if len(attempts) >= limit:
            return RateLimitDecision(
                allowed=False,
                retry_after=max(1, int(window_seconds - (now - attempts[0]))),
            )
        attempts.append(now)
        return RateLimitDecision(allowed=True, retry_after=window_seconds)

    async def clear(self, client_key: str, *, fail_closed: bool) -> None:
        self.local_attempts.pop(client_key, None)
        if self.redis is not None:
            try:
                await self.redis.delete(self._key(client_key))
            except (RedisError, OSError):
                if fail_closed:
                    raise RateLimitUnavailableError("Distributed rate limiter unavailable")
