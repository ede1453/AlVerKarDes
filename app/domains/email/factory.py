from app.core.config import settings
from app.domains.email.log_provider import LogEmailProvider
from app.domains.email.provider import EmailProvider


def get_email_provider() -> EmailProvider:
    # FastAPI dependency (not just a plain factory function) so tests can
    # override it via app.dependency_overrides to capture what would have
    # been sent, without scraping logs.
    provider = settings.EMAIL_PROVIDER.strip().lower()

    if provider == "log":
        return LogEmailProvider()

    raise ValueError(
        f"Unsupported EMAIL_PROVIDER={settings.EMAIL_PROVIDER!r} -- only "
        "'log' is wired so far. Real SMTP/third-party provider selection "
        "is a pending decision, see WIKI_ROOT ADR-013."
    )
