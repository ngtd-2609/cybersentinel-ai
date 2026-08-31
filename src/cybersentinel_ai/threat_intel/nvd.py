import re
from dataclasses import dataclass
from typing import Any

import httpx

NVD_CVE_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


@dataclass(frozen=True)
class CVERecord:
    cve_id: str
    description: str
    cvss_score: float | None
    severity: str | None
    vector: str | None
    references: tuple[str, ...]


def _validate_cve_id(cve_id: str) -> str:
    normalized = cve_id.strip().upper()

    if re.fullmatch(r"CVE-\d{4}-\d{4,}", normalized) is None:
        raise ValueError("Invalid CVE identifier")

    return normalized


def _english_description(cve: dict[str, Any]) -> str:
    descriptions = cve.get("descriptions", [])

    for description in descriptions:
        if description.get("lang") == "en":
            return str(description.get("value", ""))

    return ""


def _extract_cvss(
    cve: dict[str, Any],
) -> tuple[float | None, str | None, str | None]:
    metrics = cve.get("metrics", {})

    metric_groups = (
        "cvssMetricV40",
        "cvssMetricV31",
        "cvssMetricV30",
        "cvssMetricV2",
    )

    for group_name in metric_groups:
        group = metrics.get(group_name, [])

        if not group:
            continue

        metric = group[0]
        cvss_data = metric.get("cvssData", {})

        score = cvss_data.get("baseScore")
        severity = (
            cvss_data.get("baseSeverity")
            or metric.get("baseSeverity")
        )
        vector = cvss_data.get("vectorString")

        return (
            float(score) if score is not None else None,
            str(severity) if severity is not None else None,
            str(vector) if vector is not None else None,
        )

    return None, None, None


def parse_nvd_response(
    payload: dict[str, Any],
) -> CVERecord | None:
    vulnerabilities = payload.get("vulnerabilities", [])

    if not vulnerabilities:
        return None

    cve = vulnerabilities[0].get("cve", {})

    cve_id = str(cve.get("id", ""))

    if not cve_id:
        return None

    score, severity, vector = _extract_cvss(cve)

    references = tuple(
        str(reference["url"])
        for reference in cve.get("references", [])
        if reference.get("url")
    )

    return CVERecord(
        cve_id=cve_id,
        description=_english_description(cve),
        cvss_score=score,
        severity=severity,
        vector=vector,
        references=references,
    )


def fetch_cve(
    cve_id: str,
    api_key: str | None = None,
    timeout: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> CVERecord | None:
    normalized = _validate_cve_id(cve_id)

    headers = {}

    if api_key:
        headers["apiKey"] = api_key

    with httpx.Client(
        timeout=timeout,
        transport=transport,
    ) as client:
        response = client.get(
            NVD_CVE_API_URL,
            params={"cveId": normalized},
            headers=headers,
        )

        response.raise_for_status()

    return parse_nvd_response(response.json())
