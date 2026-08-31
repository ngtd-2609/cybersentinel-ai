from collections.abc import Callable
from dataclasses import asdict, dataclass

from cybersentinel_ai.threat_intel.attack_mapping import (
    AttackTechnique,
    map_attack_label,
)
from cybersentinel_ai.threat_intel.nvd import CVERecord, fetch_cve


@dataclass(frozen=True)
class ThreatContext:
    predicted_label: str
    attack_techniques: tuple[dict[str, str], ...]
    cve: dict[str, object] | None
    vulnerability_context: float


def cvss_to_vulnerability_context(
    cvss_score: float | None,
) -> float:
    if cvss_score is None:
        return 0.0

    score = float(cvss_score)

    if not 0.0 <= score <= 10.0:
        raise ValueError("CVSS score must be between 0 and 10")

    return round(score / 10.0, 4)


def enrich_threat_context(
    predicted_label: str,
    cve_id: str | None = None,
    nvd_api_key: str | None = None,
    cve_fetcher: Callable[..., CVERecord | None] = fetch_cve,
) -> ThreatContext:
    techniques: tuple[AttackTechnique, ...] = map_attack_label(
        predicted_label
    )

    technique_data = tuple(
        asdict(technique)
        for technique in techniques
    )

    cve_record = None

    if cve_id:
        cve_record = cve_fetcher(
            cve_id,
            api_key=nvd_api_key,
        )

    vulnerability_context = cvss_to_vulnerability_context(
        cve_record.cvss_score if cve_record else None
    )

    return ThreatContext(
        predicted_label=predicted_label,
        attack_techniques=technique_data,
        cve=asdict(cve_record) if cve_record else None,
        vulnerability_context=vulnerability_context,
    )
