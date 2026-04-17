# pyright: reportUnnecessaryTypeIgnoreComment=false

from __future__ import annotations

import contextlib
from math import inf
from typing import TYPE_CHECKING, Optional, cast

import anyio
from anyio import create_memory_object_stream
from anyio.streams.stapled import StapledObjectStream

if TYPE_CHECKING:
    from types import TracebackType

    from litestar.types import (
        ASGIApp,
        LifeSpanReceiveMessage,  # noqa: F401
        LifeSpanSendMessage,
        LifeSpanShutdownEvent,
        LifeSpanStartupEvent,
    )


class LifeSpanHandler:
    def __init__(self, app: ASGIApp) -> None:
        self.stream_send = StapledObjectStream[Optional["LifeSpanSendMessage"]](*create_memory_object_stream(inf))  # type: ignore[arg-type]
        self.stream_receive = StapledObjectStream["LifeSpanReceiveMessage"](*create_memory_object_stream(inf))  # type: ignore[arg-type]
        self.app = app
        self._exit_stack = contextlib.AsyncExitStack()

    async def __aenter__(self) -> LifeSpanHandler:
        async with contextlib.AsyncExitStack() as exit_stack:
            await exit_stack.enter_async_context(self.stream_send)
            await exit_stack.enter_async_context(self.stream_receive)

            self._tg = await exit_stack.enter_async_context(anyio.create_task_group())
            with anyio.CancelScope() as cs:
                self._tg.start_soon(self.lifespan, cs)
                await self.wait_startup()
            exit_stack.push_async_callback(self.wait_shutdown)
            self._exit_stack = exit_stack.pop_all()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._exit_stack.__aexit__(exc_type, exc_value, traceback)

    async def receive(self) -> LifeSpanSendMessage:
        message = await self.stream_send.receive()
        return cast("LifeSpanSendMessage", message)

    async def wait_startup(self) -> None:
        pass

    async def wait_shutdown(self) -> None:
        pass

    async def lifespan(self, cs: anyio.CancelScope) -> None:
        pass
