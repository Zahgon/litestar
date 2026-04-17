from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from functools import cached_property
from re import Pattern
from typing import TYPE_CHECKING, Final, Literal

from litestar.constants import DEFAULT_ALLOWED_CORS_HEADERS

__all__ = ("CORSConfig",)


if TYPE_CHECKING:
    from litestar.types import Method


# this is just a UUID, so we can be sure it's not contained within the string we're
# calling '.replace' on
_RE_ESCAPE_PLACEHOLDER: Final = uuid.uuid4().hex


@dataclass
class CORSConfig:
    """Configuration for CORS (Cross-Origin Resource Sharing).

    To enable CORS, pass an instance of this class to the :class:`Litestar <litestar.app.Litestar>` constructor using the
    'cors_config' key.
    """

    allow_origins: list[str] = field(default_factory=lambda: ["*"])
    """List of origins that are allowed.

    Can use '*' in any component of the path, e.g. 'domain.*'. Sets the 'Access-Control-Allow-Origin' header.
    """
    allow_methods: list[Literal["*"] | Method] = field(default_factory=lambda: ["*"])
    """List of allowed HTTP methods.

    Sets the 'Access-Control-Allow-Methods' header.
    """
    allow_headers: list[str] = field(default_factory=lambda: ["*"])
    """List of allowed headers.

    Sets the 'Access-Control-Allow-Headers' header.
    """
    allow_credentials: bool = field(default=False)
    """Boolean dictating whether or not to set the 'Access-Control-Allow-Credentials' header."""
    allow_origin_regex: str | None = field(default=None)
    """Regex to match origins against."""
    expose_headers: list[str] = field(default_factory=list)
    """List of headers that are exposed via the 'Access-Control-Expose-Headers' header."""
    max_age: int = field(default=600)
    """Response caching TTL in seconds, defaults to 600.

    Sets the 'Access-Control-Max-Age' header.
    """

    def __post_init__(self) -> None:
        self.allow_headers = [v.lower() for v in self.allow_headers]

    @cached_property
    def allowed_origins_regex(self) -> Pattern[str]:
        """Get or create a compiled regex for allowed origins.

        Returns:
            A compiled regex of the allowed path.
        """
        pass

    @cached_property
    def is_allow_all_origins(self) -> bool:
        """Get a cached boolean flag dictating whether all origins are allowed.

        Returns:
            Boolean dictating whether all origins are allowed.
        """
        pass

    @cached_property
    def is_allow_all_methods(self) -> bool:
        """Get a cached boolean flag dictating whether all methods are allowed.

        Returns:
            Boolean dictating whether all methods are allowed.
        """
        pass

    @cached_property
    def is_allow_all_headers(self) -> bool:
        """Get a cached boolean flag dictating whether all headers are allowed.

        Returns:
            Boolean dictating whether all headers are allowed.
        """
        pass

    @cached_property
    def preflight_headers(self) -> dict[str, str]:
        """Get cached pre-flight headers.

        Returns:
            A dictionary of headers to set on the response object.
        """
        pass

    @cached_property
    def simple_headers(self) -> dict[str, str]:
        """Get cached simple headers.

        Returns:
            A dictionary of headers to set on the response object.
        """
        pass

    def is_origin_allowed(self, origin: str) -> bool:
        """Check whether a given origin is allowed.

        Args:
            origin: An origin header value.

        Returns:
            Boolean determining whether an origin is allowed.
        """
        pass
