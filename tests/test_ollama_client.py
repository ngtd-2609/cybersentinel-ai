import httpx
import pytest

from cybersentinel_ai.rag.ollama_client import OllamaClient


def test_ollama_generate():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"

        payload = request.read().decode()

        assert "qwen2.5:3b" in payload
        assert "Analyze this alert" in payload

        return httpx.Response(
            200,
            json={
                "model": "qwen2.5:3b",
                "response": "SOC analysis result",
                "done": True,
            },
        )

    client = OllamaClient(
        transport=httpx.MockTransport(handler),
    )

    result = client.generate("Analyze this alert")

    assert result.model == "qwen2.5:3b"
    assert result.response == "SOC analysis result"
    assert result.done is True


def test_empty_prompt():
    client = OllamaClient()

    with pytest.raises(ValueError):
        client.generate("   ")
