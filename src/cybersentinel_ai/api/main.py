from collections import defaultdict, deque
from time import monotonic

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from cybersentinel_ai.api.audit_routes import router as audit_router
from cybersentinel_ai.api.copilot_routes import router as copilot_router
from cybersentinel_ai.api.dashboard_routes import router as dashboard_router
from cybersentinel_ai.api.incident_routes import router as incident_router
from cybersentinel_ai.api.metrics import configure_metrics
from cybersentinel_ai.api.routes import router
from cybersentinel_ai.api.user_admin_routes import router as user_admin_router
from cybersentinel_ai.api.user_status_routes import router as user_status_router
from cybersentinel_ai.auth.router import router as auth_router
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import get_db

settings = get_settings()
login_failures: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered network intrusion detection and SOC assistant.",
    docs_url=None if settings.environment.lower() == "production" else "/docs",
    redoc_url=None if settings.environment.lower() == "production" else "/redoc",
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_host_list,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


@app.middleware("http")
async def security_headers(request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if settings.environment.lower() == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.middleware("http")
async def login_rate_limit(request, call_next) -> Response:
    if request.method != "POST" or request.url.path != "/auth/login":
        return await call_next(request)

    forwarded_for = request.headers.get("X-Forwarded-For")
    if settings.environment.lower() == "production" and forwarded_for:
        client_key = forwarded_for.split(",", maxsplit=1)[0].strip()
    else:
        client_key = request.client.host if request.client else "unknown"
    now = monotonic()
    failures = login_failures[client_key]
    window = settings.login_rate_limit_window_seconds

    while failures and now - failures[0] >= window:
        failures.popleft()

    if len(failures) >= settings.login_rate_limit_attempts:
        retry_after = max(1, int(window - (now - failures[0])))
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many login attempts. Try again later."},
            headers={"Retry-After": str(retry_after)},
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    response = await call_next(request)
    if response.status_code == status.HTTP_200_OK:
        login_failures.pop(client_key, None)
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        failures.append(now)
    return response

app.include_router(router)
app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(copilot_router)
app.include_router(incident_router)
app.include_router(user_admin_router)
app.include_router(user_status_router)
app.include_router(dashboard_router)
configure_metrics(app)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "cybersentinel-ai",
    }


@app.get("/ready")
def readiness_check(database: Session = Depends(get_db)) -> dict[str, str]:
    try:
        database.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc

    return {
        "status": "ready",
        "service": "cybersentinel-ai",
        "database": "connected",
    }
