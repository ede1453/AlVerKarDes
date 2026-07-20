from app.core.config import settings
from app.domains.billing.mock_provider import MockPaymentProvider
from app.domains.billing.provider import PaymentProvider
from app.domains.billing.stripe_provider import StripePaymentProvider


def get_payment_provider() -> PaymentProvider:
    # FastAPI dependency (not just a plain factory function) so tests can
    # override it via app.dependency_overrides -- same reasoning as
    # app/domains/email/factory.py::get_email_provider (CLIENT-002f).
    provider = settings.PAYMENT_PROVIDER.strip().lower()

    if provider == "mock":
        return MockPaymentProvider()

    if provider == "stripe":
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError(
                "PAYMENT_PROVIDER=stripe but STRIPE_SECRET_KEY is empty -- "
                "real Stripe integration requires a real credential and "
                "user approval, see WIKI_ROOT ADR-016."
            )
        return StripePaymentProvider()

    raise ValueError(
        f"Unsupported PAYMENT_PROVIDER={settings.PAYMENT_PROVIDER!r} -- only "
        "'mock' is usable so far. Real Stripe selection is a pending "
        "decision, see WIKI_ROOT ADR-016."
    )
