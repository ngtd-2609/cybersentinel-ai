import os
import re
from dataclasses import dataclass

import httpx

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_TIMEOUT = 300.0

OLLAMA_URL_ENV = "CYBERSENTINEL_OLLAMA_URL"
OLLAMA_MODEL_ENV = "CYBERSENTINEL_OLLAMA_MODEL"
OLLAMA_TIMEOUT_ENV = "CYBERSENTINEL_OLLAMA_TIMEOUT"


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
        transport: httpx.BaseTransport | None = None,
    ) -> None:
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

        self.base_url = resolved_base_url.rstrip("/")
        self.model = resolved_model
        self.timeout = timeout
        self.transport = transport

    def generate(
        self,
        prompt: str,
        system: str | None = None,
    ) -> OllamaResponse:
        prompt = prompt.strip()

        if not prompt:
            raise ValueError("prompt must not be empty")

        payload: dict[str, object] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system:
            payload["system"] = system

        with httpx.Client(
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            response = client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )

            response.raise_for_status()
            data = response.json()

        raw_response = str(data.get("response", ""))

        return OllamaResponse(
            model=str(data.get("model", self.model)),
            response=strip_thinking(raw_response),
            done=bool(data.get("done", False)),
        )
