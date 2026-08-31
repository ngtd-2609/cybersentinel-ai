from fastapi.testclient import TestClient

from cybersentinel_ai.api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "cybersentinel-ai",
    }
