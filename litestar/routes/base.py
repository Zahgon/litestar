from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from uuid import UUID

import msgspec

from litestar.exceptions import ImproperlyConfiguredException
from litestar.types.internal_types import PathParameterDefinition
from litestar.utils import join_paths, normalize_path

ScopeT = TypeVar("ScopeT", bound="BaseScope")

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar.types import BaseScope, Receive, Send


def _parse_datetime(value: str) -> datetime:
    pass


def _parse_date(value: str) -> date:
    pass


def _parse_time(value: str) -> time:
    pass


def _parse_timedelta(value: str) -> timedelta:
    pass


param_match_regex = re.compile(r"{(.*?)}")

param_type_map = {
    "str": str,
    "int": int,
    "float": float,
    "uuid": UUID,
    "decimal": Decimal,
    "date": date,
    "datetime": datetime,
    "time": time,
    "timedelta": timedelta,
    "path": Path,
}


parsers_map: dict[Any, Callable[[Any], Any]] = {
    float: float,
    int: int,
    Decimal: Decimal,
    UUID: UUID,
    date: _parse_date,
    datetime: _parse_datetime,
    time: _parse_time,
    timedelta: _parse_timedelta,
}


class BaseRoute(ABC, Generic[ScopeT]):
    """Base Route class used by Litestar.

    It's an abstract class meant to be extended.
    """

    __slots__ = (
        "app",
        "handler_names",
        "methods",
        "path",
        "path_components",
        "path_format",
        "path_parameters",
        "scope_type",
    )

    def __init__(
        self,
        *,
        path: str,
    ) -> None:
        """Initialize the route.

        Args:
            path: Base path of the route
        """
        self.path, self.path_format, self.path_components, self.path_parameters = self._parse_path(path)

    @abstractmethod
    async def handle(self, scope: ScopeT, receive: Receive, send: Send) -> None:
        """ASGI App of the route.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.

        Returns:
            None
        """
        raise NotImplementedError("Route subclasses must implement handle which serves as the ASGI app entry point")

    @staticmethod
    def _validate_path_parameter(param: str, path: str) -> None:
        """Validate that a path parameter adheres to the required format and datatypes.

        Raises:
            ImproperlyConfiguredException: If the parameter has an invalid format.
        """
        pass

    @classmethod
    def _parse_path(
        cls, path: str
    ) -> tuple[str, str, list[str | PathParameterDefinition], dict[str, PathParameterDefinition]]:
        """Normalize and parse a path.

        Splits the path into a list of components, parsing any that are path parameters. Also builds the OpenAPI
        compatible path, which does not include the type of the path parameters.

        Returns:
            A 3-tuple of the normalized path, the OpenAPI formatted path, and the list of parsed components.
        """
        pass
