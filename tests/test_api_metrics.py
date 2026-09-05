from fastapi.testclient import TestClient

from cybersentinel_ai.api.main import app
from cybersentinel_ai.db.database import get_db

client = TestClient(app)


def test_metrics_endpoint():
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200

    body = response.text

    assert "cybersentinel_http_requests_total" in body
    assert "cybersentinel_http_request_duration_seconds" in body
    assert 'path="/health"' in body
    assert "cybersentinel_dependency_up" in body


def test_metrics_use_route_templates_instead_of_resource_ids():
    class Database:
        def get(self, _model, _identifier):
            return None

    app.dependency_overrides[get_db] = lambda: Database()
    try:
        client.get("/events/999999")
    finally:
        app.dependency_overrides.pop(get_db, None)
    body = client.get("/metrics").text

    assert 'path="/events/{event_id}"' in body
    assert 'path="/events/999999"' not in body
