from abc import ABC, abstractmethod


class CacheRepository(ABC):
    backend = "abstract"

    @abstractmethod
    def get(self, key: str):
        raise NotImplementedError

    @abstractmethod
    def set(self, *, key: str, value: dict, ttl_seconds: int):
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def clear(self):
        raise NotImplementedError

    @abstractmethod
    def status(self):
        raise NotImplementedError
