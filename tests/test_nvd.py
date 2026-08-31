import httpx
import pytest

from cybersentinel_ai.threat_intel.nvd import (
    NVD_CVE_API_URL,
    fetch_cve,
    parse_nvd_response,
)

SAMPLE_RESPONSE = {
    "vulnerabilities": [
        {
            "cve": {
                "id": "CVE-2024-0001",
                "descriptions": [
                    {
                        "lang": "en",
                        "value": "Example vulnerability.",
                    }
                ],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "cvssData": {
                                "baseScore": 9.8,
                                "baseSeverity": "CRITICAL",
                                "vectorString": (
                                    "CVSS:3.1/AV:N/AC:L/PR:N/"
                                    "UI:N/S:U/C:H/I:H/A:H"
                                ),
                            }
                        }
                    ]
                },
                "references": [
                    {"url": "https://example.com/advisory"},
                ],
            }
        }
    ]
}


def test_parse_nvd_response():
    record = parse_nvd_response(SAMPLE_RESPONSE)

    assert record is not None
    assert record.cve_id == "CVE-2024-0001"
    assert record.description == "Example vulnerability."
    assert record.cvss_score == pytest.approx(9.8)
    assert record.severity == "CRITICAL"
    assert record.vector is not None
    assert record.references == ("https://example.com/advisory",)


def test_parse_empty_nvd_response():
    assert parse_nvd_response({"vulnerabilities": []}) is None


def test_fetch_cve():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(NVD_CVE_API_URL)
        assert request.url.params["cveId"] == "CVE-2024-0001"

        return httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
        )

    transport = httpx.MockTransport(handler)

    record = fetch_cve(
        "cve-2024-0001",
        transport=transport,
    )

    assert record is not None
    assert record.cve_id == "CVE-2024-0001"
    assert record.cvss_score == pytest.approx(9.8)


def test_fetch_cve_api_key():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["apiKey"] == "test-key"

        return httpx.Response(
            200,
            json=SAMPLE_RESPONSE,
        )

    record = fetch_cve(
        "CVE-2024-0001",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )

    assert record is not None


def test_invalid_cve_id():
    with pytest.raises(ValueError):
        fetch_cve("not-a-cve")
