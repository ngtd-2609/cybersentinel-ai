from dataclasses import dataclass


@dataclass(frozen=True)
class AttackTechnique:
    technique_id: str
    technique_name: str
    tactic: str


ATTACK_MAPPING: dict[str, tuple[AttackTechnique, ...]] = {
    "DDoS": (
        AttackTechnique(
            technique_id="T1498",
            technique_name="Network Denial of Service",
            tactic="Impact",
        ),
    ),
    "DoS GoldenEye": (
        AttackTechnique(
            technique_id="T1498",
            technique_name="Network Denial of Service",
            tactic="Impact",
        ),
    ),
    "DoS Hulk": (
        AttackTechnique(
            technique_id="T1498",
            technique_name="Network Denial of Service",
            tactic="Impact",
        ),
    ),
    "DoS Slowhttptest": (
        AttackTechnique(
            technique_id="T1498",
            technique_name="Network Denial of Service",
            tactic="Impact",
        ),
    ),
    "DoS slowloris": (
        AttackTechnique(
            technique_id="T1498",
            technique_name="Network Denial of Service",
            tactic="Impact",
        ),
    ),
    "PortScan": (
        AttackTechnique(
            technique_id="T1046",
            technique_name="Network Service Discovery",
            tactic="Discovery",
        ),
    ),
    "FTP-Patator": (
        AttackTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="Credential Access",
        ),
    ),
    "SSH-Patator": (
        AttackTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="Credential Access",
        ),
    ),
    "Web Attack - Brute Force": (
        AttackTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="Credential Access",
        ),
    ),
    "Web Attack - Sql Injection": (
        AttackTechnique(
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application",
            tactic="Initial Access",
        ),
    ),
    "Web Attack - XSS": (
        AttackTechnique(
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application",
            tactic="Initial Access",
        ),
    ),
    "Heartbleed": (
        AttackTechnique(
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application",
            tactic="Initial Access",
        ),
    ),
}


def map_attack_label(
    label: str,
) -> tuple[AttackTechnique, ...]:
    if label == "BENIGN":
        return ()

    return ATTACK_MAPPING.get(label, ())
