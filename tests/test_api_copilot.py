from fastapi.testclient import TestClient

from cybersentinel_ai.api.copilot_routes import get_copilot
from cybersentinel_ai.api.main import app
from cybersentinel_ai.rag.copilot import (
    CopilotAnswer,
    CopilotSource,
)


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


app.dependency_overrides[get_copilot] = override_get_copilot

client = TestClient(app)


def test_copilot_api():
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
