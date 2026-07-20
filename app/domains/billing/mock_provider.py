import logging
import sys
import uuid

from app.domains.billing.provider import CheckoutResult

logger = logging.getLogger("app.billing")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # Same silent-root-logger fix as app/domains/email/log_provider.py
    # (CLIENT-002f, found live) -- nothing in this app calls
    # logging.basicConfig()/dictConfig(), so an unconfigured logger.info()
    # call here would be silently dropped without an explicit handler.
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False


class MockPaymentProvider:
    """BILL-001: no real money moves. Always succeeds, synchronously --
    does NOT simulate Stripe's real async webhook-confirmation flow, that
    is a deliberately deferred design question (see ADR-016). Swapping in
    a real provider later only needs a new class behind the same
    PaymentProvider interface plus one branch in
    app/domains/billing/factory.py -- no call site changes (same pattern
    as EmailProvider, CLIENT-002f)."""

    async def start_checkout(self, *, user_id: str, plan: str) -> CheckoutResult:
        reference = f"MOCK-{uuid.uuid4()}"
        logger.info(
            "MOCK CHECKOUT (no real payment) user_id=%s plan=%s reference=%s",
            user_id,
            plan,
            reference,
        )
        return CheckoutResult(success=True, external_reference=reference)

    async def cancel_subscription(self, *, user_id: str) -> None:
        logger.info("MOCK CANCEL (no real payment) user_id=%s", user_id)
