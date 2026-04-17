# pyright: reportUnnecessaryTypeIgnoreComment=false

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, Literal

from litestar.datastructures import Headers, MutableScopeHeaders
from litestar.enums import CompressionEncoding, ScopeType
from litestar.middleware.base import AbstractMiddleware
from litestar.middleware.compression.gzip_facade import GzipCompression
from litestar.utils.empty import value_or_default
from litestar.utils.scope.state import ScopeState

if TYPE_CHECKING:
    from litestar.config.compression import CompressionConfig
    from litestar.types import (
        ASGIApp,
        HTTPResponseStartEvent,
        Message,
        Receive,
        Scope,
        Send,
    )

    try:
        from brotli import Compressor
    except ImportError:
        Compressor = Any


class CompressionMiddleware(AbstractMiddleware):
    """Compression Middleware Wrapper.

    This is a wrapper allowing for generic compression configuration / handler middleware
    """

    def __init__(self, app: ASGIApp, config: CompressionConfig) -> None:
        """Initialize ``CompressionMiddleware``

        Args:
            app: The ``next`` ASGI app to call.
            config: An instance of CompressionConfig.
        """
        super().__init__(
            app=app, exclude=config.exclude, exclude_opt_key=config.exclude_opt_key, scopes={ScopeType.HTTP}
        )
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
        accept_encoding = Headers.from_scope(scope).get("accept-encoding", "")
        config = self.config

        if config.compression_facade.encoding in accept_encoding:
            await self.app(
                scope,
                receive,
                self.create_compression_send_wrapper(
                    send=send, compression_encoding=config.compression_facade.encoding, scope=scope
                ),
            )
            return

        if config.gzip_fallback and CompressionEncoding.GZIP in accept_encoding:
            await self.app(
                scope,
                receive,
                self.create_compression_send_wrapper(
                    send=send, compression_encoding=CompressionEncoding.GZIP, scope=scope
                ),
            )
            return

        await self.app(scope, receive, send)

    def create_compression_send_wrapper(
        self,
        send: Send,
        compression_encoding: Literal[CompressionEncoding.BROTLI, CompressionEncoding.GZIP, CompressionEncoding.ZSTD]
        | str,
        scope: Scope,
    ) -> Send:
        """Wrap ``send`` to handle brotli compression.

        Args:
            send: The ASGI send function.
            compression_encoding: The compression encoding used.
            scope: The ASGI connection scope

        Returns:
            An ASGI send function.
        """
        pass
