from __future__ import annotations

import asyncio
import importlib.resources as importlib_resources
from abc import ABC
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from litestar.channels.backends.base import ChannelsBackend

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Iterable

    from redis.asyncio import Redis
    from redis.asyncio.client import PubSub

_resource_path = importlib_resources.files("litestar.channels.backends")
_PUBSUB_PUBLISH_SCRIPT = (_resource_path / "_redis_pubsub_publish.lua").read_text()
_FLUSHALL_STREAMS_SCRIPT = (_resource_path / "_redis_flushall_streams.lua").read_text()
_XADD_EXPIRE_SCRIPT = (_resource_path / "_redis_xadd_expire.lua").read_text()


class _LazyEvent:
    """A lazy proxy to asyncio.Event that only creates the event once it's accessed.

    It ensures that the Event is created within a running event loop. If it's not, there can be an issue where a future
    within the event itself is attached to a different loop.

    This happens in our tests and could also happen when a user creates an instance of the backend outside an event loop
    in their application.
    """

    def __init__(self) -> None:
        self.__event: asyncio.Event | None = None

    @property
    def _event(self) -> asyncio.Event:
        pass

    def set(self) -> None:
        pass

    def clear(self) -> None:
        self._event.clear()

    async def wait(self) -> None:
        await self._event.wait()


class RedisChannelsBackend(ChannelsBackend, ABC):
    def __init__(self, *, redis: Redis, key_prefix: str, stream_sleep_no_subscriptions: int) -> None:
        """Base redis channels backend.

        Args:
            redis: A :class:`redis.asyncio.Redis` instance
            key_prefix: Key prefix to use for storing data in redis
            stream_sleep_no_subscriptions: Amount of time in milliseconds to pause the
                :meth:`stream_events` generator, should no subscribers exist
        """
        self._redis = redis
        self._key_prefix = key_prefix
        self._stream_sleep_no_subscriptions = stream_sleep_no_subscriptions

    def _make_key(self, channel: str) -> str:
        return f"{self._key_prefix}_{channel.upper()}"


class RedisChannelsPubSubBackend(RedisChannelsBackend):
    def __init__(
        self, *, redis: Redis, stream_sleep_no_subscriptions: int = 1, key_prefix: str = "LITESTAR_CHANNELS"
    ) -> None:
        """Redis channels backend, `Pub/Sub <https://redis.io/docs/manual/pubsub/>`_.

        This backend provides low overhead and resource usage but no support for history.

        Args:
            redis: A :class:`redis.asyncio.Redis` instance
            key_prefix: Key prefix to use for storing data in redis
            stream_sleep_no_subscriptions: Amount of time in milliseconds to pause the
                :meth:`stream_events` generator, should no subscribers exist
        """
        super().__init__(
            redis=redis, stream_sleep_no_subscriptions=stream_sleep_no_subscriptions, key_prefix=key_prefix
        )
        self.__pub_sub: PubSub | None = None
        self._publish_script = self._redis.register_script(_PUBSUB_PUBLISH_SCRIPT)
        self._has_subscribed = _LazyEvent()

    @property
    def _pub_sub(self) -> PubSub:
        pass

    async def on_startup(self) -> None:
        # this method should not do anything in this case
        pass

    async def on_shutdown(self) -> None:
        pass

    async def subscribe(self, channels: Iterable[str]) -> None:
        """Subscribe to ``channels``, and enable publishing to them"""
        pass

    async def unsubscribe(self, channels: Iterable[str]) -> None:
        """Stop listening for events on ``channels``"""
        pass

    async def publish(self, data: bytes, channels: Iterable[str]) -> None:
        """Publish ``data`` to ``channels``

        .. note::
            This operation is performed atomically, using a lua script
        """
        pass

    async def stream_events(self) -> AsyncGenerator[tuple[str, Any], None]:
        """Return a generator, iterating over events of subscribed channels as they become available.

        If no channels have been subscribed to yet via :meth:`subscribe`, sleep for ``stream_sleep_no_subscriptions``
        milliseconds.
        """
        pass

    async def get_history(self, channel: str, limit: int | None = None) -> list[bytes]:
        """Not implemented"""
        raise NotImplementedError()


class RedisChannelsStreamBackend(RedisChannelsBackend):
    def __init__(
        self,
        history: int,
        *,
        redis: Redis,
        stream_sleep_no_subscriptions: int = 1,
        cap_streams_approximate: bool = True,
        stream_ttl: int | timedelta = timedelta(seconds=60),
        key_prefix: str = "LITESTAR_CHANNELS",
    ) -> None:
        """Redis channels backend, `streams <https://redis.io/docs/data-types/streams/>`_.

        Args:
            history: Amount of messages to keep. This will set a ``MAXLEN`` to the streams
            redis: A :class:`redis.asyncio.Redis` instance
            key_prefix: Key prefix to use for streams
            stream_sleep_no_subscriptions: Amount of time in milliseconds to pause the
                :meth:`stream_events` generator, should no subscribers exist
            cap_streams_approximate: Set the streams ``MAXLEN`` using the ``~`` approximation
                operator for improved performance
            stream_ttl: TTL of a stream in milliseconds or as a timedelta. A streams TTL will be set on each publishing
                operation using ``PEXPIRE``
        """
        super().__init__(
            redis=redis, stream_sleep_no_subscriptions=stream_sleep_no_subscriptions, key_prefix=key_prefix
        )

        self._history_limit = history
        self._subscribed_channels: set[str] = set()
        self._cap_streams_approximate = cap_streams_approximate
        self._stream_ttl = stream_ttl if isinstance(stream_ttl, int) else int(stream_ttl.total_seconds() * 1000)
        self._flush_all_streams_script = self._redis.register_script(_FLUSHALL_STREAMS_SCRIPT)
        self._publish_script = self._redis.register_script(_XADD_EXPIRE_SCRIPT)
        self._has_subscribed_channels = _LazyEvent()

    async def on_startup(self) -> None:
        """Called on application startup"""

    async def on_shutdown(self) -> None:
        """Called on application shutdown"""

    async def subscribe(self, channels: Iterable[str]) -> None:
        """Subscribe to ``channels``"""
        pass

    async def unsubscribe(self, channels: Iterable[str]) -> None:
        """Unsubscribe from ``channels``"""
        pass

    async def publish(self, data: bytes, channels: Iterable[str]) -> None:
        """Publish ``data`` to ``channels``.

        .. note::
            This operation is performed atomically, using a Lua script
        """
        pass

    async def _get_subscribed_channels(self) -> set[str]:
        """Get subscribed channels. If no channels are currently subscribed, wait"""
        pass

    async def stream_events(self) -> AsyncGenerator[tuple[str, Any], None]:
        """Return a generator, iterating over events of subscribed channels as they become available.

        If no channels have been subscribed to yet via :meth:`subscribe`, sleep for ``stream_sleep_no_subscriptions``
        milliseconds.
        """
        pass

    async def get_history(self, channel: str, limit: int | None = None) -> list[bytes]:
        """Return the history of ``channels``, returning at most ``limit`` messages"""
        pass

    async def flush_all(self) -> int:
        """Delete all stream keys with the ``key_prefix``.

        .. important::
            This method is incompatible with redis clusters
        """
        pass
