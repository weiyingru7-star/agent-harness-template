import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import error, request


@dataclass(frozen=True)
class ProviderResult:
    output: str
    metadata: dict[str, Any] | None = None


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    pass


class LLMProvider(Protocol):
    id: str

    def generate_text(self, prompt: str) -> ProviderResult:
        ...

    def generate_json(self, prompt: str) -> ProviderResult:
        ...

    def smoke_test(self) -> ProviderResult:
        ...

    def generate(self, prompt: str, structured: bool = False) -> ProviderResult:
        ...


class MockLLMProvider:
    id = "mock"

    def generate_text(self, prompt: str) -> ProviderResult:
        cleaned_prompt = " ".join(prompt.split())
        return ProviderResult(
            output=f"Mock LLM response for: {cleaned_prompt}",
            metadata={"provider": self.id},
        )

    def generate_json(self, prompt: str) -> ProviderResult:
        cleaned_prompt = " ".join(prompt.split())
        return ProviderResult(
            output=json.dumps(
                {
                    "ok": True,
                    "provider": self.id,
                    "echo": cleaned_prompt,
                }
            ),
            metadata={"provider": self.id},
        )

    def smoke_test(self) -> ProviderResult:
        return self.generate_text("smoke")

    def generate(self, prompt: str, structured: bool = False) -> ProviderResult:
        if structured:
            return self.generate_json(prompt)
        return self.generate_text(prompt)


class OpenAICompatibleProvider:
    id = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def _validate_configuration(self) -> None:
        missing = []
        if not self.base_url:
            missing.append("base_url")
        if not self.api_key:
            missing.append("api_key")
        if not self.model:
            missing.append("model")
        if missing:
            missing_text = ", ".join(missing)
            raise ProviderConfigurationError(
                f"OpenAI-compatible provider is not configured: missing {missing_text}"
            )

    def generate_text(self, prompt: str) -> ProviderResult:
        return self._request_chat_completion(prompt=prompt, structured=False)

    def generate_json(self, prompt: str) -> ProviderResult:
        return self._request_chat_completion(prompt=prompt, structured=True)

    def smoke_test(self) -> ProviderResult:
        return self.generate_text("smoke")

    def generate(self, prompt: str, structured: bool = False) -> ProviderResult:
        if structured:
            return self.generate_json(prompt)
        return self.generate_text(prompt)

    def _request_chat_completion(self, prompt: str, structured: bool) -> ProviderResult:
        self._validate_configuration()
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
            with request.urlopen(http_request, timeout=self.timeout) as response:
                response_body = response.read().decode("utf-8")
        except error.URLError as exc:
            raise ProviderRequestError(
                "OpenAI-compatible provider request failed"
            ) from exc

        try:
            parsed = json.loads(response_body)
            content = parsed["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ProviderRequestError(
                "OpenAI-compatible provider returned an invalid response"
            ) from exc

        return ProviderResult(
            output=content,
            metadata={"provider": self.id, "model": self.model},
        )
