import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from cybersentinel_ai.core.config import get_settings

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_TIMEOUT = 180.0
DEFAULT_NUM_PREDICT = 256

OLLAMA_URL_ENV = "CYBERSENTINEL_OLLAMA_URL"
OLLAMA_MODEL_ENV = "CYBERSENTINEL_OLLAMA_MODEL"
OLLAMA_TIMEOUT_ENV = "CYBERSENTINEL_OLLAMA_TIMEOUT"
OLLAMA_NUM_PREDICT_ENV = "CYBERSENTINEL_OLLAMA_NUM_PREDICT"


class OllamaUnavailableError(RuntimeError):
    """Raised when the local model is unavailable after bounded retries."""


class ExternalAIBlockedError(RuntimeError):
    """Raised when policy blocks an external model or sensitive data transfer."""


@dataclass(frozen=True)
class OllamaResponse:
    model: str
    response: str
    done: bool


def strip_thinking(text: str) -> str:
    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return cleaned.strip()


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        num_predict: int | None = None,
        transport: httpx.BaseTransport | None = None,
        max_retries: int | None = None,
        failure_threshold: int | None = None,
        circuit_reset_seconds: float | None = None,
        allow_external: bool | None = None,
        allow_sensitive_external: bool | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        settings = get_settings()
        resolved_base_url = (
            base_url
            or os.getenv(OLLAMA_URL_ENV)
            or DEFAULT_OLLAMA_URL
        )

        resolved_model = (
            model
            or os.getenv(OLLAMA_MODEL_ENV)
            or DEFAULT_MODEL
        )

        if timeout is None:
            timeout = float(
                os.getenv(
                    OLLAMA_TIMEOUT_ENV,
                    str(DEFAULT_TIMEOUT),
                )
            )

        if num_predict is None:
            num_predict = int(
                os.getenv(
                    OLLAMA_NUM_PREDICT_ENV,
                    str(DEFAULT_NUM_PREDICT),
                )
            )

        self.base_url = resolved_base_url.rstrip("/")
        self.model = resolved_model
        self.timeout = timeout
        self.num_predict = num_predict
        self.transport = transport
        self.max_retries = (
            settings.ollama_max_retries if max_retries is None else max_retries
        )
        self.failure_threshold = (
            settings.ollama_circuit_failure_threshold
            if failure_threshold is None
            else failure_threshold
        )
        self.circuit_reset_seconds = (
            settings.ollama_circuit_reset_seconds
            if circuit_reset_seconds is None
            else circuit_reset_seconds
        )
        self.allow_external = (
            settings.allow_external_ai if allow_external is None else allow_external
        )
        self.allow_sensitive_external = (
            settings.allow_sensitive_external_ai
            if allow_sensitive_external is None
            else allow_sensitive_external
        )
        self.sleeper = sleeper
        self.clock = clock
        self.failures = 0
        self.opened_at: float | None = None
        hostname = (urlparse(self.base_url).hostname or "").lower()
        self.is_external = hostname not in {
            "localhost",
            "127.0.0.1",
            "::1",
            "ollama",
            "host.docker.internal",
        }

    def _record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = self.clock()

    def _check_circuit(self) -> None:
        if self.opened_at is None:
            return
        if self.clock() - self.opened_at < self.circuit_reset_seconds:
            raise OllamaUnavailableError("Ollama circuit breaker is open")
        self.opened_at = None
        self.failures = 0

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        format_schema: dict[str, object] | None = None,
        contains_sensitive_data: bool = False,
    ) -> OllamaResponse:
        prompt = prompt.strip()

        if not prompt:
            raise ValueError("prompt must not be empty")
        if self.is_external and not self.allow_external:
            raise ExternalAIBlockedError("external AI endpoints are disabled by policy")
        if self.is_external and contains_sensitive_data and not self.allow_sensitive_external:
            raise ExternalAIBlockedError(
                "sensitive security context cannot be sent to external AI"
            )
        self._check_circuit()

        if self.model.lower().startswith("qwen3"):
            prompt = f"/no_think\n{prompt}"

        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": self.num_predict,
                "temperature": 0.2,
            },
        }

        if system:
            payload["system"] = system

        if format_schema:
            payload["format"] = format_schema

        data = None
        last_error: Exception | None = None
        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    response = client.post(f"{self.base_url}/api/generate", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    self.failures = 0
                    self.opened_at = None
                    break
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = exc
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code < 500 and exc.response.status_code != 429:
                        raise
                    last_error = exc
                if attempt < self.max_retries:
                    self.sleeper(0.1 * (2**attempt))

        if data is None:
            self._record_failure()
            raise OllamaUnavailableError("Ollama unavailable after retries") from last_error

        raw_response = str(data.get("response", ""))

        return OllamaResponse(
            model=str(data.get("model", self.model)),
            response=strip_thinking(raw_response),
            done=bool(data.get("done", False)),
        )
