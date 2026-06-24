from dataclasses import dataclass
from typing import Any

from app.ai_runtime.providers import LLMProvider
from app.ai_runtime.structured_output import parse_structured_output


@dataclass(frozen=True)
class LLMResponse:
    provider: str
    output: str
    structured_output: dict[str, Any] | None = None


class LLMClient:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate(self, prompt: str, structured: bool = False) -> LLMResponse:
        result = self.provider.generate(prompt=prompt, structured=structured)
        parsed_output = parse_structured_output(result.output) if structured else None
        return LLMResponse(
            provider=self.provider.id,
            output=result.output,
            structured_output=parsed_output,
        )
