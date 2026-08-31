from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from cybersentinel_ai.api.routes import router
from cybersentinel_ai.db.database import create_tables


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(
    title="CyberSentinel AI",
    version="0.1.0",
    description="AI-powered network intrusion detection and SOC assistant.",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "cybersentinel-ai",
    }
