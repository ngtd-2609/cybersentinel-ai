import pytest

from cybersentinel_ai.threat_intel.enrichment import (
    cvss_to_vulnerability_context,
    enrich_threat_context,
)
from cybersentinel_ai.threat_intel.nvd import CVERecord


def test_cvss_to_vulnerability_context():
    assert cvss_to_vulnerability_context(9.8) == pytest.approx(0.98)
    assert cvss_to_vulnerability_context(5.0) == pytest.approx(0.5)
    assert cvss_to_vulnerability_context(None) == pytest.approx(0.0)


def test_invalid_cvss_score():
    with pytest.raises(ValueError):
        cvss_to_vulnerability_context(11.0)


def test_enrich_attack_without_cve():
    context = enrich_threat_context("PortScan")

    assert context.predicted_label == "PortScan"
    assert context.attack_techniques[0]["technique_id"] == "T1046"
    assert context.cve is None
    assert context.vulnerability_context == pytest.approx(0.0)


def test_enrich_attack_with_cve():
    def fake_fetcher(
        cve_id: str,
        api_key: str | None = None,
    ) -> CVERecord:
        assert cve_id == "CVE-2024-0001"
        assert api_key == "test-key"

        return CVERecord(
            cve_id=cve_id,
            description="Example vulnerability.",
            cvss_score=9.8,
            severity="CRITICAL",
            vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            references=("https://example.com/advisory",),
        )

    context = enrich_threat_context(
        predicted_label="Web Attack - Sql Injection",
        cve_id="CVE-2024-0001",
        nvd_api_key="test-key",
        cve_fetcher=fake_fetcher,
    )

    assert context.attack_techniques[0]["technique_id"] == "T1190"
    assert context.cve is not None
    assert context.cve["cve_id"] == "CVE-2024-0001"
    assert context.vulnerability_context == pytest.approx(0.98)
