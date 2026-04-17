"""Plugin for creating and retrieving flash messages."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import litestar.exceptions
from litestar.exceptions import MissingDependencyException
from litestar.middleware import DefineMiddleware
from litestar.middleware.session import SessionMiddleware
from litestar.plugins import InitPlugin
from litestar.security.session_auth.middleware import MiddlewareWrapper
from litestar.template.base import _get_request_from_context
from litestar.utils.predicates import is_class_and_subclass

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from litestar.config.app import AppConfig
    from litestar.connection.base import ASGIConnection
    from litestar.template import TemplateConfig


@dataclass
class FlashConfig:
    """Configuration for Flash messages."""

    template_config: TemplateConfig


class FlashPlugin(InitPlugin):
    """Flash messages Plugin."""

    def __init__(self, config: FlashConfig):
        """Initialize the plugin.

        Args:
            config: Configuration for flash messages, including the template engine instance.
        """
        self.config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Register the message callable on the template engine instance.

        Args:
            app_config: The application configuration.

        Returns:
            The application configuration with the message callable registered.
        """
        pass


def flash(
    request: ASGIConnection[Any, Any, Any, Any],
    message: Any,
    category: str,
) -> None:
    request.session.setdefault("_messages", []).append({"message": message, "category": category})


def get_flashes(context: Mapping[str, Any]) -> Any:
    pass
