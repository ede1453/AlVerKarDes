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

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(
                    scope=message
                )
                for key, value in self.headers.items():
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
