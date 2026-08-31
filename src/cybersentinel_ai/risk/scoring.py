from dataclasses import dataclass


@dataclass(frozen=True)
class RiskWeights:
    classifier: float = 0.45
    anomaly: float = 0.20
    rule: float = 0.15
    asset: float = 0.10
    vulnerability: float = 0.10

    def validate(self) -> None:
        values = (
            self.classifier,
            self.anomaly,
            self.rule,
            self.asset,
            self.vulnerability,
        )

        if any(value < 0.0 for value in values):
            raise ValueError("Risk weights must be non-negative")

        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("Risk weights must sum to 1.0")


def _validate_signal(name: str, value: float) -> float:
    value = float(value)

    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")

    return value


def calculate_risk_score(
    classifier_risk: float,
    anomaly_score: float,
    rule_score: float = 0.0,
    asset_criticality: float = 0.0,
    vulnerability_context: float = 0.0,
    weights: RiskWeights | None = None,
) -> float:
    weights = weights or RiskWeights()
    weights.validate()

    classifier_risk = _validate_signal(
        "classifier_risk",
        classifier_risk,
    )
    anomaly_score = _validate_signal(
        "anomaly_score",
        anomaly_score,
    )
    rule_score = _validate_signal(
        "rule_score",
        rule_score,
    )
    asset_criticality = _validate_signal(
        "asset_criticality",
        asset_criticality,
    )
    vulnerability_context = _validate_signal(
        "vulnerability_context",
        vulnerability_context,
    )

    weighted_score = (
        weights.classifier * classifier_risk
        + weights.anomaly * anomaly_score
        + weights.rule * rule_score
        + weights.asset * asset_criticality
        + weights.vulnerability * vulnerability_context
    )

    return round(weighted_score * 100.0, 2)


def risk_severity(risk_score: float) -> str:
    score = float(risk_score)

    if not 0.0 <= score <= 100.0:
        raise ValueError("risk_score must be between 0 and 100")

    if score < 40:
        return "LOW"
    if score < 70:
        return "MEDIUM"
    if score < 90:
        return "HIGH"

    return "CRITICAL"
