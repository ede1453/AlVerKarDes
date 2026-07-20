from app.domains.billing.provider import CheckoutResult


class StripePaymentProvider:
    """BILL-001: skeleton only. Real Stripe SDK integration (checkout
    session creation, webhook signature verification, real card handling)
    is deliberately NOT written yet -- pending the user's explicit approval
    and a real STRIPE_SECRET_KEY (see ADR-016). app/domains/billing/factory.py
    never returns this class while STRIPE_SECRET_KEY is empty, so these
    methods are unreachable in the current deployment; they exist only to
    complete the PaymentProvider interface."""

    async def start_checkout(self, *, user_id: str, plan: str) -> CheckoutResult:
        raise NotImplementedError(
            "StripePaymentProvider is a skeleton -- real Stripe checkout "
            "integration is pending user approval + real credentials, see "
            "WIKI_ROOT ADR-016."
        )

    async def cancel_subscription(self, *, user_id: str) -> None:
        raise NotImplementedError(
            "StripePaymentProvider is a skeleton -- real Stripe cancellation "
            "integration is pending user approval + real credentials, see "
            "WIKI_ROOT ADR-016."
        )
