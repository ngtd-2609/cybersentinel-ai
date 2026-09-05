import json

import httpx
import pytest

from cybersentinel_ai.rag.ollama_client import (
    ExternalAIBlockedError,
    OllamaClient,
    OllamaUnavailableError,
)


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
    client = OllamaClient(allow_external=True)

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

    client = OllamaClient(allow_external=True)

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
        allow_external=True,
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


def test_ollama_retries_transient_failures_then_succeeds():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            json={"model": "qwen3:4b", "response": "Recovered", "done": True},
        )

    client = OllamaClient(
        transport=httpx.MockTransport(handler),
        max_retries=2,
        sleeper=lambda _seconds: None,
    )
    assert client.generate("Analyze alert").response == "Recovered"
    assert attempts == 3


def test_circuit_breaker_opens_and_resets():
    attempts = 0
    current_time = 100.0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("offline")

    client = OllamaClient(
        transport=httpx.MockTransport(handler),
        max_retries=0,
        failure_threshold=2,
        circuit_reset_seconds=30,
        sleeper=lambda _seconds: None,
        clock=lambda: current_time,
    )
    with pytest.raises(OllamaUnavailableError):
        client.generate("first")
    with pytest.raises(OllamaUnavailableError):
        client.generate("second")
    with pytest.raises(OllamaUnavailableError, match="circuit breaker"):
        client.generate("blocked")
    assert attempts == 2

    current_time = 131.0
    with pytest.raises(OllamaUnavailableError, match="after retries"):
        client.generate("half-open probe")
    assert attempts == 3


def test_external_ai_policy_blocks_endpoint_and_sensitive_context():
    blocked_client = OllamaClient(base_url="https://external-ai.example")
    with pytest.raises(ExternalAIBlockedError, match="disabled"):
        blocked_client.generate("summarize this alert")

    client = OllamaClient(
        base_url="https://external-ai.example",
        allow_external=True,
        allow_sensitive_external=False,
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200, json={"response": "ok", "done": True}
            )
        ),
    )
    with pytest.raises(ExternalAIBlockedError, match="sensitive"):
        client.generate("source IP 10.0.0.1", contains_sensitive_data=True)
