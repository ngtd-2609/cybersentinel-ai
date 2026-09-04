import pytest
from fastapi.testclient import TestClient

from cybersentinel_ai.api.copilot_routes import get_copilot
from cybersentinel_ai.api.main import app
from cybersentinel_ai.rag.copilot import (
    CopilotAnswer,
    CopilotSource,
)
from cybersentinel_ai.security.dependencies import get_current_user


class FakeCopilot:
    def ask(
        self,
        question: str,
        alert_context: str | None = None,
        top_k: int = 4,
    ) -> CopilotAnswer:
        assert question == "How should I investigate this scan?"
        assert alert_context == "Predicted label: PortScan"
        assert top_k == 4

        return CopilotAnswer(
            answer="Investigate the source and exposed services.",
            model="qwen2.5:3b",
            sources=(
                CopilotSource(
                    document_id="mitre-t1046",
                    title="Network Service Discovery",
                    source="MITRE ATT&CK",
                    score=1.0,
                ),
            ),
        )


def override_get_copilot() -> FakeCopilot:
    return FakeCopilot()


@pytest.fixture
def client():
    previous_copilot = app.dependency_overrides.get(get_copilot)
    previous_user = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_copilot] = override_get_copilot
    app.dependency_overrides[get_current_user] = lambda: object()
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        _restore_override(get_copilot, previous_copilot)
        _restore_override(get_current_user, previous_user)


def _restore_override(dependency, previous):
    if previous is None:
        app.dependency_overrides.pop(dependency, None)
    else:
        app.dependency_overrides[dependency] = previous


def test_copilot_api(client):
    response = client.post(
        "/copilot/ask",
        json={
            "question": "How should I investigate this scan?",
            "alert_context": "Predicted label: PortScan",
            "top_k": 4,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["model"] == "qwen2.5:3b"
    assert data["answer"] == (
        "Investigate the source and exposed services."
    )
    assert data["sources"][0]["document_id"] == "mitre-t1046"


def test_copilot_api_requires_authentication():
    previous_copilot = app.dependency_overrides.get(get_copilot)
    previous_user = app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_copilot] = override_get_copilot
    try:
        with TestClient(app) as anonymous_client:
            response = anonymous_client.post(
                "/copilot/ask",
                json={"question": "How should I investigate this scan?"},
            )
        assert response.status_code == 401
    finally:
        _restore_override(get_copilot, previous_copilot)
        _restore_override(get_current_user, previous_user)
