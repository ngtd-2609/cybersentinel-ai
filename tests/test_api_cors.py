from fastapi.testclient import TestClient

from cybersentinel_ai.api.main import app

client = TestClient(app)


def test_frontend_origin_is_allowed():
    response = client.options(
        "/dashboard/summary",
        headers={
            "Origin": "http://localhost:3002",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3002"
    )
