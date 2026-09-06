from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ThreatIntelResult:
    provider: str
    indicator: str
    reputation: str
    abuse_confidence: int | None
    country: str | None
    reports: int | None
    last_reported_at: str | None

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "indicator": self.indicator,
            "reputation": self.reputation,
            "abuse_confidence": self.abuse_confidence,
            "country": self.country,
            "reports": self.reports,
            "last_reported_at": self.last_reported_at,
        }


class ThreatIntelProvider(Protocol):
    def enrich_ip(self, ip_address: str) -> ThreatIntelResult: ...

    def health(self) -> bool: ...


class AbuseIPDBProvider:
    name = "AbuseIPDB"

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    def enrich_ip(self, ip_address: str) -> ThreatIntelResult:
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            response = client.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip_address, "maxAgeInDays": 90},
                headers={"Key": self.api_key, "Accept": "application/json"},
            )
            response.raise_for_status()
        data = response.json()["data"]
        confidence = int(data.get("abuseConfidenceScore") or 0)
        reputation = "MALICIOUS" if confidence >= 75 else "SUSPICIOUS" if confidence >= 25 else "LOW_RISK"
        return ThreatIntelResult(
            provider=self.name,
            indicator=ip_address,
            reputation=reputation,
            abuse_confidence=confidence,
            country=data.get("countryCode"),
            reports=data.get("totalReports"),
            last_reported_at=data.get("lastReportedAt"),
        )

    def health(self) -> bool:
        return bool(self.api_key)
