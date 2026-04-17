from __future__ import annotations

from typing import TYPE_CHECKING, cast

from msgspec.msgpack import encode as encode_msgpack

from litestar import Request
from litestar.constants import HTTP_RESPONSE_BODY, HTTP_RESPONSE_START
from litestar.enums import ScopeType
from litestar.utils.empty import value_or_default
from litestar.utils.scope.state import ScopeState

from .base import AbstractMiddleware

if TYPE_CHECKING:
    from litestar.config.response_cache import ResponseCacheConfig
    from litestar.handlers import HTTPRouteHandler
    from litestar.types import ASGIApp, HTTPScope, Message, Receive, Scope, Send

__all__ = ["ResponseCacheMiddleware"]


class ResponseCacheMiddleware(AbstractMiddleware):
    def __init__(self, app: ASGIApp, config: ResponseCacheConfig) -> None:
        self.config = config
        super().__init__(app=app, scopes={ScopeType.HTTP})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        route_handler = cast("HTTPRouteHandler", scope["route_handler"])

        expires_in: int | None = None
        if route_handler.cache is True:
            expires_in = self.config.default_expiration
        elif route_handler.cache is not False and isinstance(route_handler.cache, int):
            expires_in = route_handler.cache

        connection_state = ScopeState.from_scope(scope)

        messages: list[Message] = []

        async def wrapped_send(message: Message) -> None:
            pass

        await self.app(scope, receive, wrapped_send)
