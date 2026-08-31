import pytest

from cybersentinel_ai.risk.engine import assess_risk


def test_assess_risk():
    result = assess_risk(
        classifier_risk=0.9,
        classifier_confidence=0.95,
        anomaly_score=0.8,
        destination_port=22,
        flow_packets_per_second=20_000,
        syn_flag_count=12,
        rst_flag_count=0,
        flow_duration=100,
        asset_criticality=0.8,
        vulnerability_context=0.6,
    )

    assert 0.0 <= result.risk_score <= 100.0
    assert result.severity in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }
    assert result.rule_score == pytest.approx(0.70)
    assert result.requires_review is False
    assert result.rule_signals["suspicious_port"] is True


def test_low_confidence_high_anomaly_requires_review():
    result = assess_risk(
        classifier_risk=0.4,
        classifier_confidence=0.45,
        anomaly_score=0.85,
        destination_port=443,
        flow_packets_per_second=100,
        syn_flag_count=0,
        rst_flag_count=0,
        flow_duration=1000,
    )

    assert result.requires_review is True


def test_invalid_classifier_confidence():
    with pytest.raises(ValueError):
        assess_risk(
            classifier_risk=0.5,
            classifier_confidence=1.5,
            anomaly_score=0.5,
            destination_port=80,
            flow_packets_per_second=100,
            syn_flag_count=0,
            rst_flag_count=0,
            flow_duration=100,
        )
