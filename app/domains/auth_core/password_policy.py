from __future__ import annotations

from dataclasses import dataclass
import re


COMMON_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "admin123",
    "letmein123",
}


@dataclass(frozen=True)
class PasswordPolicyResult:
    valid: bool
    errors: tuple[str, ...]
    score: int


class PasswordPolicy:
    def __init__(
        self,
        *,
        minimum_length: int = 12,
        maximum_length: int = 128,
    ) -> None:
        self.minimum_length = minimum_length
        self.maximum_length = maximum_length

    def evaluate(
        self,
        password: str,
        *,
        identity_fragments: tuple[str, ...] = (),
    ) -> PasswordPolicyResult:
        errors: list[str] = []
        classes = 0

        if len(password) < self.minimum_length:
            errors.append("PASSWORD_TOO_SHORT")

        if len(password) > self.maximum_length:
            errors.append("PASSWORD_TOO_LONG")

        patterns = (
            r"[a-z]",
            r"[A-Z]",
            r"[0-9]",
            r"[^A-Za-z0-9]",
        )

        for pattern in patterns:
            if re.search(pattern, password):
                classes += 1

        if classes < 3:
            errors.append("PASSWORD_COMPLEXITY_INSUFFICIENT")

        lowered = password.casefold()

        if lowered in COMMON_PASSWORDS:
            errors.append("PASSWORD_TOO_COMMON")

        for fragment in identity_fragments:
            normalized = fragment.strip().casefold()

            if len(normalized) >= 3 and normalized in lowered:
                errors.append("PASSWORD_CONTAINS_IDENTITY")
                break

        if re.search(r"(.)\1{3,}", password):
            errors.append("PASSWORD_REPEATED_CHARACTERS")

        score = min(
            100,
            len(password) * 3 + classes * 10,
        )

        return PasswordPolicyResult(
            valid=not errors,
            errors=tuple(errors),
            score=score,
        )
