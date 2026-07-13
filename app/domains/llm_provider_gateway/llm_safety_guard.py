class LLMSafetyGuard:
    FORBIDDEN_SYSTEM_MARKERS = [
        "ignore previous instructions",
        "reveal system prompt",
        "bypass guardrails",
    ]

    def validate(self, *, system_prompt: str, user_prompt: str, guardrails: list[str]) -> list[str]:
        warnings: list[str] = []

        combined = f"{system_prompt}\n{user_prompt}".lower()

        for marker in self.FORBIDDEN_SYSTEM_MARKERS:
            if marker in combined:
                warnings.append(f"FORBIDDEN_PROMPT_MARKER:{marker}")

        if not guardrails:
            warnings.append("MISSING_GUARDRAILS")

        if "do not change assistant_decision" not in " ".join(guardrails).lower():
            warnings.append("MISSING_DECISION_IMMUTABILITY_GUARDRAIL")

        return warnings
