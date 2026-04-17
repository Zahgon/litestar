from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.constants import DEFAULT_ALLOWED_CORS_HEADERS
from litestar.datastructures import Headers, MutableScopeHeaders
from litestar.enums import HttpMethod, MediaType, ScopeType
from litestar.middleware.base import AbstractMiddleware
from litestar.response import Response
from litestar.status_codes import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

if TYPE_CHECKING:
    from litestar.config.cors import CORSConfig
    from litestar.types import ASGIApp, Message, Receive, Scope, Send

__all__ = ("CORSMiddleware",)


class CORSMiddleware(AbstractMiddleware):
    """CORS Middleware."""

    def __init__(self, app: ASGIApp, config: CORSConfig) -> None:
        """Middleware that adds CORS validation to the application.

        Args:
            app: The ``next`` ASGI app to call.
            config: An instance of :class:`CORSConfig <litestar.config.cors.CORSConfig>`
        """
        super().__init__(app=app, scopes={ScopeType.HTTP})
        self.config = config

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI callable.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        headers = Headers.from_scope(scope=scope)
        origin = headers.get("origin")

        if scope["type"] == ScopeType.HTTP and scope["method"] == HttpMethod.OPTIONS and origin:
            request = scope["litestar_app"].request_class(scope=scope, receive=receive, send=send)
            asgi_response = self._create_preflight_response(origin=origin, request_headers=headers).to_asgi_response(
                request=request
            )
            await asgi_response(scope, receive, send)
        elif origin:
            await self.app(scope, receive, self.send_wrapper(send=send, origin=origin, has_cookie="cookie" in headers))
        else:
            await self.app(scope, receive, send)

    def send_wrapper(self, send: Send, origin: str, has_cookie: bool) -> Send:
        """Wrap ``send`` to ensure that state is not disconnected.

        Args:
            has_cookie: Boolean flag dictating if the connection has a cookie set.
            origin: The value of the ``Origin`` header.
            send: The ASGI send function.

        Returns:
            An ASGI send function.
        """
        pass

    def _create_preflight_response(self, origin: str, request_headers: Headers) -> Response[str | None]:
        pass
