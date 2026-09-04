import asyncio
import os
from uuid import uuid4

import pytest

from cybersentinel_ai.security.rate_limit import LoginRateLimiter

pytestmark = pytest.mark.skipif(
    os.getenv("CYBERSENTINEL_RUN_REDIS_INTEGRATION") != "1",
    reason="requires the disposable Redis service used by CI",
)


def test_multiple_instances_share_real_redis_quota() -> None:
    redis_url = os.environ["CYBERSENTINEL_REDIS_URL"]
    prefix = f"ci-login-rate-{uuid4()}"
    first = LoginRateLimiter(redis_url, key_prefix=prefix)
    second = LoginRateLimiter(redis_url, key_prefix=prefix)

    async def exercise() -> None:
        try:
            assert (
                await first.consume("198.51.100.8", limit=2, window_seconds=60, fail_closed=True)
            ).allowed
            assert (
                await second.consume("198.51.100.8", limit=2, window_seconds=60, fail_closed=True)
            ).allowed
            blocked = await first.consume(
                "198.51.100.8", limit=2, window_seconds=60, fail_closed=True
            )
            assert not blocked.allowed
            assert blocked.retry_after > 0
            await second.clear("198.51.100.8", fail_closed=True)
        finally:
            if first.redis is not None:
                await first.redis.aclose()
            if second.redis is not None:
                await second.redis.aclose()

    asyncio.run(exercise())
