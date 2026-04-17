from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar._openapi.datastructures import OpenAPIContext
from litestar._openapi.path_item import create_path_item_for_route, merge_path_item_operations
from litestar.constants import OPENAPI_JSON_HANDLER_NAME
from litestar.enums import MediaType
from litestar.exceptions import ImproperlyConfiguredException, NotFoundException
from litestar.handlers import get
from litestar.openapi.plugins import JsonRenderPlugin
from litestar.plugins import InitPlugin
from litestar.plugins.base import ReceiveRoutePlugin
from litestar.response import Response
from litestar.router import Router
from litestar.routes import HTTPRoute
from litestar.status_codes import HTTP_404_NOT_FOUND

if TYPE_CHECKING:
    from litestar.app import Litestar
    from litestar.config.app import AppConfig
    from litestar.connection import Request
    from litestar.handlers import HTTPRouteHandler
    from litestar.openapi.config import OpenAPIConfig
    from litestar.openapi.plugins import OpenAPIRenderPlugin
    from litestar.openapi.spec import OpenAPI, PathItem
    from litestar.routes import BaseRoute


def handle_schema_path_not_found(path: str = "/") -> Response:
    """Handler for returning HTML formatted errors from not-found schema paths.

    This preserves backward compatibility with the Controller-based OpenAPI implementation.
    """
    pass


class OpenAPIPlugin(InitPlugin, ReceiveRoutePlugin):
    __slots__ = (
        "_openapi",
        "_openapi_config",
        "_openapi_schema",
        "app",
        "included_routes",
    )

    def __init__(self, app: Litestar) -> None:
        self.app = app
        self.included_routes: dict[str, HTTPRoute] = {}
        self._openapi_config: OpenAPIConfig | None = None
        self._openapi: OpenAPI | None = None
        self._openapi_schema: dict[str, object] | None = None

    def _build_openapi(self) -> OpenAPI:
        openapi_config = self.openapi_config

        if openapi_config.create_examples:
            from litestar._openapi.schema_generation.examples import ExampleFactory

            ExampleFactory.seed_random(openapi_config.random_seed)

        openapi = openapi_config.to_openapi_schema()
        context = OpenAPIContext(openapi_config=openapi_config, plugins=self.app.plugins.openapi)
        path_items: dict[str, PathItem] = {}
        for route in self.included_routes.values():
            path = route.path_format or "/"
            path_item = create_path_item_for_route(context, route)
            if existing_path_item := path_items.get(path):
                path_item = merge_path_item_operations(existing_path_item, path_item, for_path=path)
            path_items[path] = path_item

        openapi.paths = path_items
        openapi.components.schemas = context.schema_registry.generate_components_schemas()
        return openapi

    def provide_openapi(self) -> OpenAPI:
        if not self._openapi:
            self._openapi = self._build_openapi()
        return self._openapi

    def provide_openapi_schema(self) -> dict[str, Any]:
        if not self._openapi_schema:
            self._openapi_schema = self.provide_openapi().to_schema()
        return self._openapi_schema

    def create_openapi_router(self) -> Router:
        """Create a router for serving OpenAPI documentation and schema files.

        For each OpenAPI render plugin, a route is created to serve the plugin's
        documentation site.

        A handler is added for serving a 404 page for any schema path that is not
        configured by a plugin.

        A handler is added for serving the JSON OpenAPI schema file if it is not configured.

        For each plugin, the plugin's `receive_router` method is called with the router
        instance.

        Returns:
            The router.
        """
        pass

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        pass

    @property
    def openapi_config(self) -> OpenAPIConfig:
        pass

    def receive_route(self, route: BaseRoute) -> None:
        pass
