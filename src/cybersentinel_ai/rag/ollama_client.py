from dataclasses import dataclass

import httpx

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"


@dataclass(frozen=True)
class OllamaResponse:
    model: str
    response: str
    done: bool


class OllamaClient:
    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
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

        return OllamaResponse(
            model=str(data.get("model", self.model)),
            response=str(data.get("response", "")).strip(),
            done=bool(data.get("done", False)),
        )
