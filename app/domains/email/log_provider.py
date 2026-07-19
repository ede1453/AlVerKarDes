import logging
import sys

logger = logging.getLogger("app.email")
logger.setLevel(logging.INFO)
if not logger.handlers:
    # CLIENT-002f, found live: nothing in this app calls
    # logging.basicConfig()/dictConfig() -- uvicorn configures its OWN
    # named loggers (uvicorn/uvicorn.access/uvicorn.error) but the root
    # logger is otherwise untouched, has no handler, and defaults to
    # WARNING. An unconfigured logger.info() call here was silently
    # dropped (confirmed: real container, real docker logs, nothing
    # appeared) -- this handler makes the log-provider's output actually
    # visible without changing logging behavior anywhere else in the app.
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logger.addHandler(_handler)
    logger.propagate = False


class LogEmailProvider:
    """CLIENT-002f: dev-safe default -- logs the email instead of actually
    sending it. No real SMTP/third-party provider (SendGrid, Postmark, ...)
    is wired yet; that choice is explicitly deferred pending the user's
    decision (see WIKI_ROOT/05-Decisions/ADR-013-CLIENT-002f-Sifre-Sifirlama.md).
    Swapping in a real provider later only needs a new class behind the
    same EmailProvider interface plus one branch in
    app/domains/email/factory.py -- no call site changes."""

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info(
            "EMAIL (log-provider, NOT actually sent) to=%s subject=%s\n%s",
            to,
            subject,
            body,
        )
