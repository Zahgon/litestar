# pyright: reportUnnecessaryTypeIgnoreComment=false

try:
    import rich_click as click
except ImportError:
    import click  # type: ignore[no-redef]
from rich.prompt import Confirm

from litestar import Litestar
from litestar.cli._utils import LitestarCLIException, LitestarGroup, console
from litestar.middleware import DefineMiddleware
from litestar.middleware.session import SessionMiddleware
from litestar.middleware.session.server_side import ServerSideSessionBackend
from litestar.utils import is_class_and_subclass

__all__ = ("clear_sessions_command", "delete_session_command", "get_session_backend", "sessions_group")


def get_session_backend(app: Litestar) -> ServerSideSessionBackend:
    """Get the session backend used by a ``Litestar`` app."""
    for middleware in app.middleware:
        if isinstance(middleware, DefineMiddleware):
            if not is_class_and_subclass(middleware.middleware, SessionMiddleware):
                continue
            backend = middleware.kwargs["backend"]
            if not isinstance(backend, ServerSideSessionBackend):
                raise LitestarCLIException("Only server-side backends are supported")
            return backend
    raise LitestarCLIException("Session middleware not installed")


@click.group(cls=LitestarGroup, name="sessions")
def sessions_group() -> None:
    """Manage server-side sessions."""


@sessions_group.command("delete")  # type: ignore[untyped-decorator]
@click.argument("session-id")
def delete_session_command(session_id: str, app: Litestar) -> None:
    """Delete a specific session."""
    pass


@sessions_group.command("clear")  # type: ignore[untyped-decorator]
def clear_sessions_command(app: Litestar) -> None:
    """Delete all sessions."""
    pass
