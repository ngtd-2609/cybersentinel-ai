import pytest

from cybersentinel_ai.rag.copilot import SOCCopilot
from cybersentinel_ai.rag.ollama_client import OllamaResponse


class FakeOllamaClient:
    def generate(
        self,
        prompt: str,
        system: str | None = None,
    ) -> OllamaResponse:
        assert "scan open ports" in prompt
        assert "Retrieved security knowledge" in prompt
        assert system is not None

        return OllamaResponse(
            model="qwen2.5:3b",
            response="Investigate the source and exposed services.",
            done=True,
        )


def test_soc_copilot_answer():
    copilot = SOCCopilot(
        llm_client=FakeOllamaClient(),  # type: ignore[arg-type]
    )

    result = copilot.ask(
        "How should I investigate scan open ports activity?",
        alert_context="Predicted label: PortScan",
    )

    assert result.answer == (
        "Investigate the source and exposed services."
    )
    assert result.model == "qwen2.5:3b"
    assert result.sources
    assert any(
        source.document_id == "mitre-t1046"
        for source in result.sources
    )


def test_soc_copilot_empty_question():
    copilot = SOCCopilot(
        llm_client=FakeOllamaClient(),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError):
        copilot.ask("   ")
