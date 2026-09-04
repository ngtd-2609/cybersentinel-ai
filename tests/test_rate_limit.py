import asyncio

from redis.exceptions import ConnectionError

from cybersentinel_ai.security.rate_limit import (
    LoginRateLimiter,
    RateLimitUnavailableError,
)


class SharedRedis:
    def __init__(self):
        self.counts: dict[str, int] = {}

    async def eval(self, _script, _number_of_keys, key, window_ms):
        self.counts[key] = self.counts.get(key, 0) + 1
        return [self.counts[key], window_ms]

    async def delete(self, key):
        self.counts.pop(key, None)


class UnavailableRedis:
    async def eval(self, *_args):
        raise ConnectionError("unavailable")


def test_two_limiter_instances_share_a_distributed_quota():
    shared = SharedRedis()
    first = LoginRateLimiter(None, key_prefix="test")
    second = LoginRateLimiter(None, key_prefix="test")
    first.redis = shared
    second.redis = shared

    async def exercise():
        assert (await first.consume("client", limit=2, window_seconds=60, fail_closed=True)).allowed
        assert (
            await second.consume("client", limit=2, window_seconds=60, fail_closed=True)
        ).allowed
        assert not (
            await first.consume("client", limit=2, window_seconds=60, fail_closed=True)
        ).allowed
        await second.clear("client", fail_closed=True)
        assert (await first.consume("client", limit=2, window_seconds=60, fail_closed=True)).allowed

    asyncio.run(exercise())


def test_distributed_limiter_fails_closed_when_redis_is_unavailable():
    limiter = LoginRateLimiter(None)
    limiter.redis = UnavailableRedis()

    async def exercise():
        try:
            await limiter.consume("client", limit=2, window_seconds=60, fail_closed=True)
        except RateLimitUnavailableError:
            return
        raise AssertionError("expected the limiter to fail closed")

    asyncio.run(exercise())
