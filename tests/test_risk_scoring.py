import pytest

from cybersentinel_ai.risk.scoring import (
    RiskWeights,
    calculate_risk_score,
    risk_severity,
)


def test_calculate_risk_score():
    score = calculate_risk_score(
        classifier_risk=0.9,
        anomaly_score=0.8,
        rule_score=0.7,
        asset_criticality=0.6,
        vulnerability_context=0.5,
    )

    assert score == pytest.approx(78.0)
    assert risk_severity(score) == "HIGH"


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "LOW"),
        (39, "LOW"),
        (40, "MEDIUM"),
        (69, "MEDIUM"),
        (70, "HIGH"),
        (89, "HIGH"),
        (90, "CRITICAL"),
        (100, "CRITICAL"),
    ],
)
def test_risk_severity(score, expected):
    assert risk_severity(score) == expected


def test_invalid_signal():
    with pytest.raises(ValueError):
        calculate_risk_score(
            classifier_risk=1.2,
            anomaly_score=0.5,
        )


def test_invalid_weights():
    weights = RiskWeights(
        classifier=0.5,
        anomaly=0.5,
        rule=0.5,
        asset=0.0,
        vulnerability=0.0,
    )

    with pytest.raises(ValueError):
        calculate_risk_score(
            classifier_risk=0.5,
            anomaly_score=0.5,
            weights=weights,
        )
