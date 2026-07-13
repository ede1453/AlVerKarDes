import os
from dataclasses import dataclass


@dataclass
class LLMProviderSettings:
    enable_external_llm_providers: bool = False
    openai_api_key: str | None = None
    local_provider_enabled: bool = False

    @classmethod
    def from_environment(cls):
        return cls(
            enable_external_llm_providers=os.getenv("ENABLE_EXTERNAL_LLM_PROVIDERS", "false").lower() == "true",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            local_provider_enabled=os.getenv("ENABLE_LOCAL_LLM_PROVIDER", "false").lower() == "true",
        )
