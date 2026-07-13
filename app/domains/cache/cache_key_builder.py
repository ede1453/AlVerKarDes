import hashlib
import json


class CacheKeyBuilder:
    def build(self, *, namespace: str, payload: dict) -> str:
        normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"
