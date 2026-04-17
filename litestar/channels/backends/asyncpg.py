from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from functools import partial
from typing import TYPE_CHECKING, overload

import asyncpg

from litestar.channels import ChannelsBackend
from litestar.exceptions import ImproperlyConfiguredException

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable, Iterable


class AsyncPgChannelsBackend(ChannelsBackend):
    _listener_conn: asyncpg.Connection

    @overload
    def __init__(self, dsn: str) -> None: ...

    @overload
    def __init__(
        self,
        *,
        make_connection: Callable[[], Awaitable[asyncpg.Connection]],
    ) -> None: ...

    def __init__(
        self,
        dsn: str | None = None,
        *,
        make_connection: Callable[[], Awaitable[asyncpg.Connection]] | None = None,
    ) -> None:
        if not (dsn or make_connection):
            raise ImproperlyConfiguredException("Need to specify dsn or make_connection")

        self._subscribed_channels: set[str] = set()
        self._exit_stack = AsyncExitStack()
        self._connect = make_connection or partial(asyncpg.connect, dsn=dsn)
        self._queue: asyncio.Queue[tuple[str, bytes]] | None = None

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

    def _listener(self, /, connection: asyncpg.Connection, pid: int, channel: str, payload: object) -> None:
        pass
