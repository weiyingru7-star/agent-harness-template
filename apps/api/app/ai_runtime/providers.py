import json
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request


@dataclass(frozen=True)
class ProviderResult:
    output: str


class LLMProvider(Protocol):
    id: str

    def generate(self, prompt: str, structured: bool = False) -> ProviderResult:
        ...


class MockLLMProvider:
    id = "mock"

    def generate(self, prompt: str, structured: bool = False) -> ProviderResult:
        cleaned_prompt = " ".join(prompt.split())
        if structured:
            return ProviderResult(
                output=json.dumps(
                    {
                        "ok": True,
                        "provider": self.id,
                        "echo": cleaned_prompt,
                    }
                )
            )
        return ProviderResult(output=f"Mock LLM response for: {cleaned_prompt}")


class OpenAICompatibleProvider:
    id = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, structured: bool = False) -> ProviderResult:
        if not self.base_url or not self.api_key:
            raise RuntimeError("OpenAI-compatible provider is not configured")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if structured:
            payload["response_format"] = {"type": "json_object"}

        data = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=30) as response:
                response_body = response.read().decode("utf-8")
        except error.URLError as exc:
            raise RuntimeError("OpenAI-compatible provider request failed") from exc

        parsed = json.loads(response_body)
        content = parsed["choices"][0]["message"]["content"]
        return ProviderResult(output=content)
