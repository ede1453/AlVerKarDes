from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.production_hardening import security_headers


class SecurityHeadersMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        production: bool,
    ) -> None:
        self.app = app
        self.headers = security_headers(
            production=production
        )
        # CLIENT-001 (ADR-010): the CSP's original "this backend is a pure
        # JSON API, never serves HTML/scripts" assumption stopped being true
        # once /ui (a real static HTML+JS page) was added -- default-src
        # 'none' silently blocked the page's <script src>/<link> under CSP,
        # so no click handler ever ran (confirmed live: no console error,
        # just a dead page -- CSP violations aren't always surfaced as JS
        # exceptions). /ui only needs same-origin script/style/fetch, never
        # inline, so this stays properly restrictive (no 'unsafe-inline').
        self.ui_headers = dict(self.headers)
        self.ui_headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        path = scope.get("path", "")
        response_headers = (
            self.ui_headers
            if path.startswith("/ui")
            else self.headers
        )

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(
                    scope=message
                )
                for key, value in response_headers.items():
                    if key not in headers:
                        headers[key] = value
            await send(message)

        await self.app(
            scope,
            receive,
            send_wrapper,
        )


class RequestSizeLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        maximum_bytes: int,
    ) -> None:
        self.app = app
        self.maximum_bytes = maximum_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(
            b"content-length"
        )

        if (
            content_length is not None
            and int(content_length)
            > self.maximum_bytes
        ):
            await send({
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (
                        b"content-type",
                        b"application/json",
                    )
                ],
            })
            await send({
                "type": "http.response.body",
                "body": (
                    b'{"detail":"Request body too large"}'
                ),
            })
            return

        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed
            message = await receive()

            if message["type"] == "http.request":
                consumed += len(
                    message.get("body", b"")
                )

                if consumed > self.maximum_bytes:
                    return {
                        "type": "http.disconnect"
                    }

            return message

        await self.app(
            scope,
            limited_receive,
            send,
        )
