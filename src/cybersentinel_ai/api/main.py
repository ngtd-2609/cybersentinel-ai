import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cybersentinel_ai.api.audit_routes import router as audit_router
from cybersentinel_ai.api.copilot_routes import router as copilot_router
from cybersentinel_ai.api.dashboard_routes import router as dashboard_router
from cybersentinel_ai.api.incident_routes import router as incident_router
from cybersentinel_ai.api.metrics import configure_metrics
from cybersentinel_ai.api.routes import router
from cybersentinel_ai.api.user_admin_routes import router as user_admin_router
from cybersentinel_ai.api.user_status_routes import router as user_status_router
from cybersentinel_ai.auth.router import router as auth_router

app = FastAPI(
    title="CyberSentinel AI",
    version="0.1.0",
    description="AI-powered network intrusion detection and SOC assistant.",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CYBERSENTINEL_CORS_ORIGINS",
        "http://localhost:3002",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
