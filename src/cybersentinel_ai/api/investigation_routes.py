from datetime import UTC, datetime, timedelta
from ipaddress import ip_address
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from cybersentinel_ai.api.schemas import (
    AssetCreate,
    AssetRead,
    ResponseActionCreate,
    ResponseActionRead,
    ThreatIntelRead,
)
from cybersentinel_ai.audit.service import log_action
from cybersentinel_ai.core.config import get_settings
from cybersentinel_ai.db.database import atomic, get_db
from cybersentinel_ai.db.models import (
    Asset,
    IncidentTimeline,
    ResponseAction,
    ThreatIntelCache,
)
from cybersentinel_ai.db.repository import get_incident
from cybersentinel_ai.security.dependencies import get_current_user
from cybersentinel_ai.security.rbac import UserRole, require_role
from cybersentinel_ai.threat_intel.providers import AbuseIPDBProvider

router = APIRouter(tags=["Investigation"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def _can_operate_incident(user, incident) -> bool:
    return user.role in {
        UserRole.ADMIN.value,
        UserRole.SENIOR_ANALYST.value,
        UserRole.ANALYST.value,
    } or (
        incident.workspace == "SANDBOX" and incident.owner_user_id == user.id
    )


@router.get("/assets", response_model=list[AssetRead])
def list_assets(
    database: DatabaseSession,
    _: object = Depends(get_current_user),
    query: str | None = Query(default=None, max_length=255),
) -> list[Asset]:
    statement = select(Asset).order_by(Asset.criticality, Asset.hostname)
    if query:
        statement = statement.where(
            Asset.hostname.ilike(f"%{query.strip()}%")
            | Asset.primary_ip.ilike(f"%{query.strip()}%")
            | Asset.id.ilike(f"%{query.strip()}%")
        )
    return list(database.scalars(statement.limit(200)).all())


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(
    asset_id: str,
    database: DatabaseSession,
    _: object = Depends(get_current_user),
) -> Asset:
    asset = database.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/assets", response_model=AssetRead, status_code=201)
def create_asset(
    payload: AssetCreate,
    database: DatabaseSession,
    current_user=Depends(require_role(UserRole.ADMIN)),
) -> Asset:
    if database.get(Asset, payload.id) is not None:
        raise HTTPException(status_code=409, detail="Asset already exists")
    with atomic(database):
        asset = Asset(**payload.model_dump())
        database.add(asset)
        database.flush()
        log_action(
            database,
            current_user.id,
            "CREATE_ASSET",
            f"Created asset {asset.id}",
            "ASSET",
            None,
            commit=False,
        )
    database.refresh(asset)
    return asset


@router.get(
    "/incidents/{incident_id}/responses",
    response_model=list[ResponseActionRead],
)
def list_responses(
    incident_id: int,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> list[ResponseAction]:
    incident = get_incident(
        database, incident_id, user_id=current_user.id, role=current_user.role
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return list(
        database.scalars(
            select(ResponseAction)
            .where(ResponseAction.incident_id == incident_id)
            .order_by(ResponseAction.created_at.desc())
        ).all()
    )


@router.post(
    "/incidents/{incident_id}/responses/simulate",
    response_model=ResponseActionRead,
    status_code=201,
)
def simulate_response(
    incident_id: int,
    payload: ResponseActionCreate,
    database: DatabaseSession,
    current_user=Depends(get_current_user),
) -> ResponseAction:
    incident = get_incident(
        database, incident_id, user_id=current_user.id, role=current_user.role
    )
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not _can_operate_incident(current_user, incident):
        raise HTTPException(status_code=403, detail="Incident response is not permitted")
    if incident.workspace == "DEMO" and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Demo incidents are read-only")

    now = datetime.now(UTC)
    label = payload.action.replace("_", " ").title()
    with atomic(database):
        response = ResponseAction(
            incident_id=incident.id,
            requested_by=current_user.id,
            approved_by=current_user.id,
            action=payload.action,
            target=payload.target,
            status="SIMULATED_SUCCESS",
            result=f"{label} completed safely in simulation mode",
            simulation=True,
            completed_at=now,
        )
        database.add(response)
        database.flush()
        database.add(
            IncidentTimeline(
                incident_id=incident.id,
                action="SIMULATED_RESPONSE",
                description=f"{label}: {payload.target} (simulation only)",
            )
        )
        log_action(
            database,
            current_user.id,
            "SIMULATE_RESPONSE_ACTION",
            f"{payload.action} against {payload.target} for incident {incident.id}",
            "INCIDENT",
            incident.id,
            commit=False,
        )
    database.refresh(response)
    return response


@router.get("/threat-intel/ip/{indicator}", response_model=ThreatIntelRead)
def enrich_ip(
    indicator: str,
    database: DatabaseSession,
    _: object = Depends(get_current_user),
) -> ThreatIntelRead:
    try:
        normalized = str(ip_address(indicator))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid IP address") from exc
    now = datetime.now(UTC)
    cached = database.scalar(
        select(ThreatIntelCache).where(
            ThreatIntelCache.provider == "AbuseIPDB",
            ThreatIntelCache.indicator_type == "ip",
            ThreatIntelCache.indicator == normalized,
            ThreatIntelCache.expires_at > now,
        )
    )
    if cached is not None:
        return ThreatIntelRead(**cached.payload, cached=True)

    settings = get_settings()
    if settings.abuseipdb_api_key is None:
        return ThreatIntelRead(
            provider="AbuseIPDB",
            indicator=normalized,
            reputation="UNAVAILABLE",
            cached=False,
            available=False,
            error="Provider key is not configured",
        )
    provider = AbuseIPDBProvider(
        settings.abuseipdb_api_key.get_secret_value(),
        timeout=settings.threat_intel_timeout_seconds,
    )
    try:
        result = provider.enrich_ip(normalized)
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return ThreatIntelRead(
            provider="AbuseIPDB",
            indicator=normalized,
            reputation="UNAVAILABLE",
            cached=False,
            available=False,
            error="Threat-intelligence provider is temporarily unavailable",
        )
    payload = result.as_dict()
    with atomic(database):
        stale = database.scalar(
            select(ThreatIntelCache).where(
                ThreatIntelCache.provider == "AbuseIPDB",
                ThreatIntelCache.indicator_type == "ip",
                ThreatIntelCache.indicator == normalized,
            )
        )
        if stale is None:
            stale = ThreatIntelCache(
                provider="AbuseIPDB", indicator_type="ip", indicator=normalized
            )
            database.add(stale)
        stale.payload = payload
        stale.fetched_at = now
        stale.expires_at = now + timedelta(
            seconds=settings.threat_intel_cache_ttl_seconds
        )
    return ThreatIntelRead(**payload, cached=False)
