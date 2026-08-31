from fastapi.testclient import TestClient

from cybersentinel_ai.api.main import app

client = TestClient(app)


def test_metrics_endpoint():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "cybersentinel_http_requests_total" in body
    assert "cybersentinel_http_request_duration_seconds" in body
    assert 'path="/health"' in body
