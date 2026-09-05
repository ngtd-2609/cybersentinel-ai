import json

from redis.asyncio import Redis

from cybersentinel_ai.core.config import get_settings


async def publish_update(payload: dict) -> None:
    settings = get_settings()
    if not settings.redis_url:
        return
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.publish(settings.realtime_channel, json.dumps(payload))
    finally:
        await client.aclose()
