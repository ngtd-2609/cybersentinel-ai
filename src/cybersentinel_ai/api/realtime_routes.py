import asyncio

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from starlette.responses import StreamingResponse

from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.security.dependencies import get_current_user

router = APIRouter(prefix="/stream", tags=["Real-time SOC"])


@router.get("/soc", dependencies=[Depends(get_current_user)])
async def soc_stream(request: Request) -> StreamingResponse:
    settings = get_settings()

    async def events():
        yield "event: connected\ndata: {}\n\n"
        if not settings.redis_url:
            while not await request.is_disconnected():
                await asyncio.sleep(15)
                yield ": heartbeat\n\n"
            return

        client = Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = client.pubsub()
        try:
            await pubsub.subscribe(settings.realtime_channel)
            while not await request.is_disconnected():
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=15.0
                )
                if message is None:
                    yield ": heartbeat\n\n"
                else:
                    yield f"event: soc-update\ndata: {message['data']}\n\n"
        finally:
            await pubsub.aclose()
            await client.aclose()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
