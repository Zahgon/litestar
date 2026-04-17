from __future__ import annotations

import re
from collections import defaultdict
from functools import lru_cache
from re import Pattern
from traceback import format_exc
from typing import TYPE_CHECKING, Any

from litestar._asgi.routing_trie import validate_node
from litestar._asgi.routing_trie.mapping import add_route_to_trie
from litestar._asgi.routing_trie.traversal import parse_path_to_route
from litestar._asgi.routing_trie.types import create_node
from litestar._asgi.utils import get_route_handlers
from litestar.exceptions import ImproperlyConfiguredException
from litestar.utils import normalize_path
from litestar.utils.scope.state import ScopeState

if TYPE_CHECKING:
    from litestar._asgi.routing_trie.types import RouteTrieNode
    from litestar.app import Litestar
    from litestar.routes import ASGIRoute, HTTPRoute, WebSocketRoute
    from litestar.routes.base import BaseRoute
    from litestar.types import (
        ASGIApp,
        ExceptionHandlersMap,
        LifeSpanReceive,
        LifeSpanSend,
        LifeSpanShutdownCompleteEvent,
        LifeSpanShutdownFailedEvent,
        LifeSpanStartupCompleteEvent,
        LifeSpanStartupFailedEvent,
        Method,
        Receive,
        RouteHandlerType,
        Scope,
        Send,
    )

__all__ = ("ASGIRouter",)


class ASGIRouter:
    """Litestar ASGI router.

    Handling both the ASGI lifespan events and routing of connection requests.
    """

    __slots__ = (
        "_app_exception_handlers",
        "_mount_paths_regex",
        "_mount_routes",
        "_plain_routes",
        "_registered_routes",
        "_static_routes",
        "_trie_initialized",
        "app",
        "root_route_map_node",
        "route_handler_index",
        "route_mapping",
    )

    def __init__(self, app: Litestar) -> None:
        """Initialize ``ASGIRouter``.

        Args:
            app: The Litestar app instance
        """
        self._app_exception_handlers: ExceptionHandlersMap = app.exception_handlers
        self._mount_paths_regex: Pattern | None = None
        self._mount_routes: dict[str, RouteTrieNode] = {}
        self._plain_routes: set[str] = set()
        self._registered_routes: set[HTTPRoute | WebSocketRoute | ASGIRoute] = set()
        self._trie_initialized = False
        self.app = app
        self.root_route_map_node: RouteTrieNode = create_node()
        self.route_handler_index: dict[str, RouteHandlerType] = {}
        self.route_mapping: dict[str, list[BaseRoute]] = defaultdict(list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI callable.

        The main entry point to the Router class.
        """
        scope.setdefault("path_params", {})

        path = scope["path"]
        if root_path := scope.get("root_path", ""):
            path = path.split(root_path, maxsplit=1)[-1]
        normalized_path = normalize_path(path)

        try:
            asgi_app, route_handler, scope["path"], scope["path_params"], path_template = self.handle_routing(
                path=normalized_path, method=scope.get("method")
            )
        except Exception:
            ScopeState.from_scope(scope).exception_handlers = self._app_exception_handlers
            raise
        else:
            ScopeState.from_scope(scope).exception_handlers = route_handler.exception_handlers
            scope["route_handler"] = route_handler
            scope["path_template"] = path_template
        await asgi_app(scope, receive, send)

    @lru_cache(1024)  # noqa: B019
    def handle_routing(
        self, path: str, method: Method | None
    ) -> tuple[ASGIApp, RouteHandlerType, str, dict[str, Any], str]:
        """Handle routing for a given path / method combo. This method is meant to allow easy caching.

        Args:
            path: The path of the request.
            method: The scope's method, if any.

        Returns:
            A tuple composed of the ASGIApp of the route, the route handler instance, the resolved and normalized path and any parsed path params.
        """
        pass

    def _store_handler_to_route_mapping(self, route: BaseRoute) -> None:
        """Store the mapping of route handlers to routes and to route handler names.

        Args:
            route: A Route instance.

        Returns:
            None
        """
        pass

    def construct_routing_trie(self) -> None:
        """Create a map of the app's routes.

        This map is used in the asgi router to route requests.
        """
        pass

    async def lifespan(self, receive: LifeSpanReceive, send: LifeSpanSend) -> None:
        """Handle the ASGI "lifespan" event on application startup and shutdown.

        Args:
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None.
        """
        pass
