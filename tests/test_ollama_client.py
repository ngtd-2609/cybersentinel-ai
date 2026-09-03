import json

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


def test_ollama_uses_environment_configuration(monkeypatch):
    monkeypatch.setenv(
        "CYBERSENTINEL_OLLAMA_URL",
        "http://ollama.internal:11434",
    )
    monkeypatch.setenv(
        "CYBERSENTINEL_OLLAMA_MODEL",
        "custom-model",
    )

    client = OllamaClient()

    assert client.base_url == "http://ollama.internal:11434"
    assert client.model == "custom-model"


def test_explicit_configuration_overrides_environment(monkeypatch):
    monkeypatch.setenv(
        "CYBERSENTINEL_OLLAMA_URL",
        "http://environment:11434",
    )
    monkeypatch.setenv(
        "CYBERSENTINEL_OLLAMA_MODEL",
        "environment-model",
    )

    client = OllamaClient(
        base_url="http://explicit:11434/",
        model="explicit-model",
    )

    assert client.base_url == "http://explicit:11434"
    assert client.model == "explicit-model"


def test_strip_qwen_thinking_block():
    from cybersentinel_ai.rag.ollama_client import strip_thinking

    response = """
<think>
Internal reasoning that must not reach the API user.
</think>

1. Block source IP
2. Investigate scan
3. Review exposed ports
"""

    assert strip_thinking(response) == (
        "1. Block source IP\n"
        "2. Investigate scan\n"
        "3. Review exposed ports"
    )


def test_ollama_timeout_from_environment(monkeypatch):
    monkeypatch.setenv(
        "CYBERSENTINEL_OLLAMA_TIMEOUT",
        "240",
    )

    client = OllamaClient()

    assert client.timeout == 240.0


def test_qwen3_disables_thinking_in_prompt():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read().decode())

        assert payload["think"] is False
        assert payload["prompt"].startswith("/no_think\n")

        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b",
                "response": "1. Assessment\nRansomware alert.",
                "done": True,
            },
        )

    client = OllamaClient(
        model="qwen3:4b",
        transport=httpx.MockTransport(handler),
    )

    result = client.generate("Analyze this alert")

    assert result.response.startswith("1. Assessment")


def test_ollama_sends_structured_output_schema():
    schema: dict[str, object] = {
        "type": "object",
        "properties": {"assessment": {"type": "string"}},
        "required": ["assessment"],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read().decode())
        assert payload["format"] == schema
        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b",
                "response": '{"assessment":"Critical alert"}',
                "done": True,
            },
        )

    client = OllamaClient(
        model="qwen3:4b",
        transport=httpx.MockTransport(handler),
    )

    client.generate("Analyze this alert", format_schema=schema)
