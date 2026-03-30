from __future__ import annotations

from dataclasses import dataclass

from agentshield_cli.config import LLMConfig


@dataclass(frozen=True)
class ResolvedLLMSettings:
    provider: str
    model: str
    base_url: str | None
    api_key: str | None

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)


def resolve_llm_settings(config: LLMConfig) -> ResolvedLLMSettings:
    return ResolvedLLMSettings(
        provider=config.provider,
        model=config.model,
        base_url=config.resolved_base_url(),
        api_key=config.resolved_api_key(),
    )
