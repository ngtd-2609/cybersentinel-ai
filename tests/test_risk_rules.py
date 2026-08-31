import pytest

from cybersentinel_ai.risk.rules import (
    RuleSignals,
    build_rule_signals,
    calculate_rule_score,
)


def test_calculate_rule_score():
    signals = RuleSignals(
        high_packet_rate=True,
        suspicious_port=True,
        syn_pattern=True,
    )

    assert calculate_rule_score(signals) == pytest.approx(0.70)


def test_rule_score_all_signals():
    signals = RuleSignals(
        high_packet_rate=True,
        suspicious_port=True,
        syn_pattern=True,
        reset_pattern=True,
        abnormal_flow_duration=True,
    )

    assert calculate_rule_score(signals) == pytest.approx(1.0)


def test_build_rule_signals():
    signals = build_rule_signals(
        destination_port=22,
        flow_packets_per_second=20_000,
        syn_flag_count=12,
        rst_flag_count=0,
        flow_duration=100,
    )

    assert signals.high_packet_rate is True
    assert signals.suspicious_port is True
    assert signals.syn_pattern is True
    assert signals.reset_pattern is False
    assert signals.abnormal_flow_duration is False
