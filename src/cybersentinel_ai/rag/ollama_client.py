import os
import re
from dataclasses import dataclass

import httpx

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_TIMEOUT = 180.0
DEFAULT_NUM_PREDICT = 256

OLLAMA_URL_ENV = "CYBERSENTINEL_OLLAMA_URL"
OLLAMA_MODEL_ENV = "CYBERSENTINEL_OLLAMA_MODEL"
OLLAMA_TIMEOUT_ENV = "CYBERSENTINEL_OLLAMA_TIMEOUT"
OLLAMA_NUM_PREDICT_ENV = "CYBERSENTINEL_OLLAMA_NUM_PREDICT"


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

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        format_schema: dict[str, object] | None = None,
    ) -> OllamaResponse:
        prompt = prompt.strip()

        if not prompt:
            raise ValueError("prompt must not be empty")

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
