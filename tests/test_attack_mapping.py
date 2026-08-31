from cybersentinel_ai.threat_intel.attack_mapping import map_attack_label


def test_portscan_attack_mapping():
    techniques = map_attack_label("PortScan")

    assert len(techniques) == 1
    assert techniques[0].technique_id == "T1046"
    assert techniques[0].tactic == "Discovery"


def test_brute_force_attack_mapping():
    techniques = map_attack_label("SSH-Patator")

    assert len(techniques) == 1
    assert techniques[0].technique_id == "T1110"
    assert techniques[0].tactic == "Credential Access"


def test_web_attack_mapping():
    techniques = map_attack_label("Web Attack - Sql Injection")

    assert len(techniques) == 1
    assert techniques[0].technique_id == "T1190"
    assert techniques[0].tactic == "Initial Access"


def test_benign_has_no_attack_mapping():
    assert map_attack_label("BENIGN") == ()


def test_unknown_label_has_no_attack_mapping():
    assert map_attack_label("Unknown Attack") == ()
