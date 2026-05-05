"""Middleware для security headers.

Добавляет к каждому ответу заголовки безопасности:
- X-Content-Type-Options: nosniff      (браузер не должен угадывать MIME)
- X-Frame-Options: DENY                (защита от clickjacking)
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: ограничивает доступ к API браузера
- Content-Security-Policy: пока не задаём (потребует тонкой настройки под фронт)

В продакшене Cloudflare/Nginx тоже могут добавлять эти заголовки —
не страшно, дублирование безвредно.
"""

from starlette.types import ASGIApp, Receive, Scope, Send


# Заголовки добавляются ко всем HTTP-ответам.
# Значения подобраны под web-приложение средней строгости.
_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (
        b"permissions-policy",
        # Запрещаем доступ к чувствительным API браузера.
        # microphone разрешим позже когда добавим STT.
        b"camera=(), geolocation=(), microphone=(), payment=()",
    ),
]


class SecurityHeadersMiddleware:
    """Добавляет security headers к каждому HTTP-ответу."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # Добавляем заголовки если они ещё не присутствуют
                existing_keys = {h[0].lower() for h in headers}
                for name, value in _SECURITY_HEADERS:
                    if name not in existing_keys:
                        headers.append((name, value))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
