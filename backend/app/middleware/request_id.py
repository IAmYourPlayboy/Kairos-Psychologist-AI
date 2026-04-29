"""ASGI-middleware для генерации и проброса X-Request-ID."""

import uuid
from collections.abc import Callable

from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIDMiddleware:
    """Добавляет X-Request-ID к каждому HTTP-ответу.

    Если клиент передал заголовок — используется его значение,
    иначе генерируется UUID4.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Ищем X-Request-ID в заголовках запроса
        request_id: str | None = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-request-id":
                request_id = header_value.decode("latin-1")
                break

        if not request_id:
            request_id = uuid.uuid4().hex

        async def send_with_request_id(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_request_id)
