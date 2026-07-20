from dataclasses import dataclass
from typing import Protocol


@dataclass
class CheckoutResult:
    success: bool
    external_reference: str


class PaymentProvider(Protocol):
    async def start_checkout(self, *, user_id: str, plan: str) -> CheckoutResult: ...
    async def cancel_subscription(self, *, user_id: str) -> None: ...
