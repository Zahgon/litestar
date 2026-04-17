from __future__ import annotations

from asyncio import Queue
from collections import defaultdict, deque
from typing import TYPE_CHECKING, Any

from litestar.channels.backends.base import ChannelsBackend

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Iterable


class MemoryChannelsBackend(ChannelsBackend):
    """An in-memory channels backend"""

    def __init__(self, history: int = 0) -> None:
        self._max_history_length = history
        self._channels: set[str] = set()
        self._queue: Queue[tuple[str, bytes]] | None = None
        self._history: defaultdict[str, deque[bytes]] = defaultdict(lambda: deque(maxlen=self._max_history_length))

    async def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass

    async def publish(self, data: bytes, channels: Iterable[str]) -> None:
        """Publish ``data`` to ``channels``. If a channel has not yet been subscribed to,
        this will be a no-op.

        Args:
            data: Data to publish
            channels: Channels to publish to

        Returns:
            None

        Raises:
            RuntimeError: If ``on_startup`` has not been called yet
        """
        pass

    async def subscribe(self, channels: Iterable[str]) -> None:
        """Subscribe to ``channels``, and enable publishing to them"""
        pass

    async def unsubscribe(self, channels: Iterable[str]) -> None:
        """Unsubscribe from ``channels``"""
        pass

    async def stream_events(self) -> AsyncGenerator[tuple[str, Any], None]:
        """Return a generator, iterating over events of subscribed channels as they become available"""
        pass

    async def get_history(self, channel: str, limit: int | None = None) -> list[bytes]:
        """Return the event history of ``channel``, at most ``limit`` entries"""
        pass
