from dataclasses import dataclass, field


@dataclass
class LLMStreamingRequest:
    text: str
    event_type: str = "token"
    chunk_size: int = 24
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMStreamEvent:
    event: str
    data: dict
    index: int
