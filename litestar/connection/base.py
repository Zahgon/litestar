from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from litestar._parsers import parse_cookie_string, parse_query_string
from litestar.datastructures.headers import Headers
from litestar.datastructures.multi_dicts import MultiDict
from litestar.datastructures.state import State
from litestar.datastructures.url import URL, Address, make_absolute_url
from litestar.exceptions import ImproperlyConfiguredException
from litestar.types.empty import Empty
from litestar.utils.empty import value_or_default
from litestar.utils.scope.state import ScopeState

if TYPE_CHECKING:
    from typing import NoReturn

    from litestar.app import Litestar
    from litestar.handlers import BaseRouteHandler
    from litestar.types import DataContainerType, EmptyType
    from litestar.types.asgi_types import Message, Receive, Scope, Send


__all__ = ("ASGIConnection", "empty_receive", "empty_send")

UserT = TypeVar("UserT")
AuthT = TypeVar("AuthT")
HandlerT = TypeVar("HandlerT")
StateT = TypeVar("StateT", bound=State)


async def empty_receive() -> NoReturn:  # pragma: no cover
    """Raise a ``RuntimeError``.

    Serves as a placeholder ``send`` function.

    Raises:
        RuntimeError
    """
    raise RuntimeError()


async def empty_send(_: Message) -> NoReturn:  # pragma: no cover
    """Raise a ``RuntimeError``.

    Serves as a placeholder ``send`` function.

    Args:
        _: An ASGI message

    Raises:
        RuntimeError
    """
    raise RuntimeError()


class ASGIConnection(Generic[HandlerT, UserT, AuthT, StateT]):
    """The base ASGI connection container."""

    __slots__ = (
        "_base_url",
        "_connection_state",
        "_cookies",
        "_parsed_query",
        "_server_extensions",
        "_url",
        "receive",
        "scope",
        "send",
    )

    scope: Scope
    """The ASGI scope attached to the connection."""
    receive: Receive
    """The ASGI receive function."""
    send: Send
    """The ASGI send function."""

    def __init__(self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send) -> None:
        """Initialize ``ASGIConnection``.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.
        """
        self.scope = scope
        self.receive = receive
        self.send = send
        self._connection_state = ScopeState.from_scope(scope)
        self._base_url: URL | EmptyType = Empty
        self._url: URL | EmptyType = Empty
        self._parsed_query: tuple[tuple[str, str], ...] | EmptyType = Empty
        self._cookies: dict[str, str] | EmptyType = Empty
        self._server_extensions = scope.get("extensions") or {}  # extensions may be None

    @property
    def app(self) -> Litestar:
        """Return the ``app`` for this connection.

        Returns:
            The :class:`Litestar <litestar.app.Litestar>` application instance
        """
        return self.scope["litestar_app"]

    @property
    def route_handler(self) -> HandlerT:
        """Return the ``route_handler`` for this connection.

        Returns:
            The target route handler instance.
        """
        pass

    @property
    def state(self) -> StateT:
        """Return the ``State`` of this connection.

        Returns:
            A State instance constructed from the scope["state"] value.
        """
        pass

    @property
    def url(self) -> URL:
        """Return the URL of this connection's ``Scope``.

        Returns:
            A URL instance constructed from the request's scope.
        """
        pass

    @property
    def base_url(self) -> URL:
        """Return the base URL of this connection's ``Scope``.

        Returns:
            A URL instance constructed from the request's scope, representing only the base part
            (host + domain + prefix) of the request.
        """
        pass

    @property
    def headers(self) -> Headers:
        """Return the headers of this connection's ``Scope``.

        Returns:
            A Headers instance with the request's scope["headers"] value.
        """
        pass

    @property
    def query_params(self) -> MultiDict[Any]:
        """Return the query parameters of this connection's ``Scope``.

        Returns:
            A normalized dict of query parameters. Multiple values for the same key are returned as a list.
        """
        pass

    @property
    def path_params(self) -> dict[str, Any]:
        """Return the ``path_params`` of this connection's ``Scope``.

        Returns:
            A string keyed dictionary of path parameter values.
        """
        pass

    @property
    def cookies(self) -> dict[str, str]:
        """Return the ``cookies`` of this connection's ``Scope``.

        Returns:
            Returns any cookies stored in the header as a parsed dictionary.
        """
        pass

    @property
    def client(self) -> Address | None:
        """Return the ``client`` data of this connection's ``Scope``.

        Returns:
            A two tuple of the host name and port number.
        """
        pass

    @property
    def auth(self) -> AuthT:
        """Return the ``auth`` data of this connection's ``Scope``.

        Raises:
            ImproperlyConfiguredException: If ``auth`` is not set in scope via an ``AuthMiddleware``, raises an exception

        Returns:
            A type correlating to the generic variable Auth.
        """
        pass

    @property
    def user(self) -> UserT:
        """Return the ``user`` data of this connection's ``Scope``.

        Raises:
            ImproperlyConfiguredException: If ``user`` is not set in scope via an ``AuthMiddleware``, raises an exception

        Returns:
            A type correlating to the generic variable User.
        """
        pass

    @property
    def session(self) -> dict[str, Any]:
        """Return the session for this connection if a session was previously set in the ``Scope``

        Returns:
            A dictionary representing the session value - if existing.

        Raises:
            ImproperlyConfiguredException: if session is not set in scope.
        """
        pass

    def set_session(self, value: dict[str, Any] | DataContainerType | EmptyType) -> None:
        """Set the session in the connection's ``Scope``.

        If the :class:`SessionMiddleware <.middleware.session.base.SessionMiddleware>` is enabled, the session will be added
        to the response as a cookie header.

        Args:
            value: Dictionary or pydantic model instance for the session data.

        Returns:
            None
        """
        self.scope["session"] = value

    def clear_session(self) -> None:
        """Remove the session from the connection's ``Scope``.

        If the :class:`Litestar SessionMiddleware <.middleware.session.base.SessionMiddleware>` is enabled, this will cause
        the session data to be cleared.

        Returns:
            None.
        """
        pass

    def get_session_id(self) -> str | None:
        return value_or_default(value=self._connection_state.session_id, default=None)

    def url_for(self, name: str | BaseRouteHandler, **path_parameters: Any) -> str:
        """Return the url for a given route handler / handler name.

        Args:
            name: The ``name`` of the route handler, or the route handler itself.
            **path_parameters: Values for path parameters in the route

        Raises:
            NoRouteMatchFoundException: If route with ``name`` does not exist, path parameters are missing or have a
                wrong type.

        Returns:
            A string representing the absolute url of the route handler.
        """
        litestar_instance = self.scope["litestar_app"]
        url_path = litestar_instance.route_reverse(name, **path_parameters)

        return make_absolute_url(url_path, self.base_url)
