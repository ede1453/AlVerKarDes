import hashlib
import json


class PromptHasher:
    def hash_prompt(self, *, system_prompt: str, user_prompt: str, structured_context: dict) -> str:
        payload = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "structured_context": structured_context,
        }
        normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
