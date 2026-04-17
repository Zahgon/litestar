from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Any

from psycopg import AsyncConnection
from psycopg.sql import SQL, Identifier

from litestar.channels.backends.base import ChannelsBackend

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Iterable


class PsycoPgChannelsBackend(ChannelsBackend):
    _listener_conn: AsyncConnection[Any]

    def __init__(self, pg_dsn: str) -> None:
        self._pg_dsn = pg_dsn
        self._subscribed_channels: set[str] = set()
        self._exit_stack = AsyncExitStack()

    async def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass

    async def publish(self, data: bytes, channels: Iterable[str]) -> None:
        pass

    async def subscribe(self, channels: Iterable[str]) -> None:
        pass

    async def unsubscribe(self, channels: Iterable[str]) -> None:
        pass

    async def stream_events(self) -> AsyncGenerator[tuple[str, bytes], None]:
        pass

    async def get_history(self, channel: str, limit: int | None = None) -> list[bytes]:
        raise NotImplementedError()
