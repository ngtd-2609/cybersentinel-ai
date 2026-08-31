from dataclasses import dataclass


@dataclass(frozen=True)
class RuleSignals:
    high_packet_rate: bool = False
    suspicious_port: bool = False
    syn_pattern: bool = False
    reset_pattern: bool = False
    abnormal_flow_duration: bool = False


RULE_WEIGHTS = {
    "high_packet_rate": 0.30,
    "suspicious_port": 0.15,
    "syn_pattern": 0.25,
    "reset_pattern": 0.15,
    "abnormal_flow_duration": 0.15,
}


def calculate_rule_score(signals: RuleSignals) -> float:
    score = 0.0

    for name, weight in RULE_WEIGHTS.items():
        if getattr(signals, name):
            score += weight

    return round(min(score, 1.0), 4)


def build_rule_signals(
    destination_port: float,
    flow_packets_per_second: float,
    syn_flag_count: float,
    rst_flag_count: float,
    flow_duration: float,
) -> RuleSignals:
    suspicious_ports = {
        21,
        22,
        23,
        25,
        53,
        80,
        110,
        135,
        139,
        443,
        445,
        1433,
        3306,
        3389,
        8080,
    }

    return RuleSignals(
        high_packet_rate=flow_packets_per_second >= 10_000,
        suspicious_port=int(destination_port) in suspicious_ports,
        syn_pattern=syn_flag_count >= 10,
        reset_pattern=rst_flag_count >= 10,
        abnormal_flow_duration=flow_duration <= 0,
    )
