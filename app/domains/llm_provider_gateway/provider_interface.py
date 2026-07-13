from abc import ABC, abstractmethod

from app.domains.llm_provider_gateway.llm_provider_models import (
    LLMGatewayRequest,
    LLMGatewayResponse,
)


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, request: LLMGatewayRequest) -> LLMGatewayResponse:
        raise NotImplementedError
