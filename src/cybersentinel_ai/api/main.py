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
from cybersentinel_ai.api.ingestion_routes import router as ingestion_router
from cybersentinel_ai.api.metrics import configure_metrics
from cybersentinel_ai.api.realtime_routes import router as realtime_router
from cybersentinel_ai.api.routes import router
from cybersentinel_ai.api.rule_routes import router as rule_router
from cybersentinel_ai.api.user_admin_routes import router as user_admin_router
from cybersentinel_ai.api.user_status_routes import router as user_status_router
from cybersentinel_ai.audit.context import (
    build_request_context,
    reset_request_context,
    set_request_context,
)
from cybersentinel_ai.auth.router import router as auth_router
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import get_db
from cybersentinel_ai.security.rate_limit import (
    LoginRateLimiter,
    RateLimitUnavailableError,
)

settings = get_settings()
login_rate_limiter = LoginRateLimiter(settings.redis_url)
login_failures = login_rate_limiter.local_attempts

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
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Idempotency-Key",
        "X-Ingestion-Key",
        "X-Request-ID",
    ],
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
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def request_audit_context(request, call_next) -> Response:
    context = build_request_context(request, trust_proxy_headers=settings.trust_proxy_headers)
    token = set_request_context(context)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = context.request_id
        return response
    finally:
        reset_request_context(token)


@app.middleware("http")
async def login_rate_limit(request, call_next) -> Response:
    if request.method != "POST" or request.url.path != "/auth/login":
        return await call_next(request)

    context = build_request_context(request, trust_proxy_headers=settings.trust_proxy_headers)
    client_key = context.ip_address or "unknown"
    try:
        decision = await login_rate_limiter.consume(
            client_key,
            limit=settings.login_rate_limit_attempts,
            window_seconds=settings.login_rate_limit_window_seconds,
            fail_closed=settings.rate_limit_fail_closed,
        )
    except RateLimitUnavailableError:
        response = JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Login protection is temporarily unavailable"},
            headers={"Retry-After": "5"},
        )
        response.headers["X-Request-ID"] = context.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    if not decision.allowed:
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many login attempts. Try again later."},
            headers={"Retry-After": str(decision.retry_after)},
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Request-ID"] = context.request_id
        return response

    response = await call_next(request)
    if response.status_code in {status.HTTP_200_OK, status.HTTP_202_ACCEPTED}:
        try:
            await login_rate_limiter.clear(client_key, fail_closed=settings.rate_limit_fail_closed)
        except RateLimitUnavailableError:
            unavailable = JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Login protection is temporarily unavailable"},
                headers={"Retry-After": "5"},
            )
            unavailable.headers["X-Request-ID"] = context.request_id
            unavailable.headers["X-Content-Type-Options"] = "nosniff"
            unavailable.headers["X-Frame-Options"] = "DENY"
            return unavailable
    return response


app.include_router(router)
app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(copilot_router)
app.include_router(incident_router)
app.include_router(ingestion_router)
app.include_router(realtime_router)
app.include_router(rule_router)
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
