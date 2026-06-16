from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class LLMError(RuntimeError):
    pass


class QuestLLM(Protocol):
    def generate(self, prompt: str) -> str:
        pass


@dataclass
class OllamaClient:
    model: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    timeout: int = 120

    def generate(self, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise LLMError(f"Could not reach Ollama at {self.base_url}. Is Ollama running?") from exc
        except TimeoutError as exc:
            raise LLMError("Ollama request timed out.") from exc

        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMError("Ollama returned invalid JSON.") from exc

        text = data.get("response")
        if not isinstance(text, str) or not text.strip():
            raise LLMError("Ollama response did not include generated text.")
        return text


def check_ollama(base_url: str = "http://localhost:11434", timeout: int = 3) -> tuple[bool, str]:
    request = urllib.request.Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status == 200:
                return True, "Ollama is reachable."
            return False, f"Ollama returned HTTP {response.status}."
    except urllib.error.URLError:
        return False, f"Ollama is not reachable at {base_url}."
    except TimeoutError:
        return False, "Ollama health check timed out."

