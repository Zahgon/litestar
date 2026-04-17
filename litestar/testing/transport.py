# pyright: reportUnnecessaryTypeIgnoreComment=false

from __future__ import annotations

from io import BytesIO
from types import GeneratorType
from typing import TYPE_CHECKING, Any, Generic, TypedDict, TypeVar, Union, cast
from urllib.parse import unquote

import anyio
from httpx import AsyncBaseTransport, BaseTransport, ByteStream, Response

from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR

if TYPE_CHECKING:
    from httpx import Request

    from litestar.testing.client import AsyncTestClient, TestClient
    from litestar.types import (
        HTTPDisconnectEvent,
        HTTPRequestEvent,
        Message,
        Receive,
        ReceiveMessage,
        Send,
        WebSocketScope,
    )


T = TypeVar("T", bound=Union["AsyncTestClient", "TestClient"])


class ConnectionUpgradeExceptionError(Exception):
    def __init__(self, scope: WebSocketScope) -> None:
        self.scope = scope


class SendReceiveContext(TypedDict):
    request_complete: bool
    response_complete: anyio.Event
    raw_kwargs: dict[str, Any]
    response_started: bool
    template: str | None
    context: Any | None


class TestClientTransport(AsyncBaseTransport, Generic[T]):
    def __init__(
        self,
        client: T,
        raise_server_exceptions: bool = False,
        root_path: str = "",
    ) -> None:
        self.client = client
        self.raise_server_exceptions = raise_server_exceptions
        self.root_path = root_path

    @staticmethod
    def create_receive(request: Request, context: SendReceiveContext) -> Receive:
        pass

    @staticmethod
    def create_send(request: Request, context: SendReceiveContext) -> Send:
        pass

    def parse_request(self, request: Request) -> dict[str, Any]:
        pass

    async def handle_async_request(self, request: Request) -> Response:
        pass


class SyncTestClientTransport(BaseTransport):
    def __init__(
        self,
        client: TestClient,
        raise_server_exceptions: bool = False,
        root_path: str = "",
    ):
        self.client = client
        self._async_transport = TestClientTransport(
            client=client,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
        )

    def handle_request(self, request: Request) -> Response:
        pass
