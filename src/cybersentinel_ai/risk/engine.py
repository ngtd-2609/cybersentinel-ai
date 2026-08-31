from dataclasses import asdict, dataclass

from cybersentinel_ai.risk.rules import (
    RuleSignals,
    build_rule_signals,
    calculate_rule_score,
)
from cybersentinel_ai.risk.scoring import (
    calculate_risk_score,
    risk_severity,
)


@dataclass(frozen=True)
class RiskAssessment:
    risk_score: float
    severity: str
    rule_score: float
    requires_review: bool
    rule_signals: dict[str, bool]


def assess_risk(
    classifier_risk: float,
    classifier_confidence: float,
    anomaly_score: float,
    destination_port: float,
    flow_packets_per_second: float,
    syn_flag_count: float,
    rst_flag_count: float,
    flow_duration: float,
    asset_criticality: float = 0.0,
    vulnerability_context: float = 0.0,
) -> RiskAssessment:
    if not 0.0 <= classifier_confidence <= 1.0:
        raise ValueError("classifier_confidence must be between 0 and 1")

    signals: RuleSignals = build_rule_signals(
        destination_port=destination_port,
        flow_packets_per_second=flow_packets_per_second,
        syn_flag_count=syn_flag_count,
        rst_flag_count=rst_flag_count,
        flow_duration=flow_duration,
    )

    rule_score = calculate_rule_score(signals)

    score = calculate_risk_score(
        classifier_risk=classifier_risk,
        anomaly_score=anomaly_score,
        rule_score=rule_score,
        asset_criticality=asset_criticality,
        vulnerability_context=vulnerability_context,
    )

    requires_review = (
        classifier_confidence < 0.60
        and anomaly_score >= 0.70
    )

    return RiskAssessment(
        risk_score=score,
        severity=risk_severity(score),
        rule_score=rule_score,
        requires_review=requires_review,
        rule_signals=asdict(signals),
    )
