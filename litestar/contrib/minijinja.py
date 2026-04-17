from __future__ import annotations

import functools
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from typing_extensions import ParamSpec

from litestar.exceptions import ImproperlyConfiguredException, MissingDependencyException, TemplateNotFoundException
from litestar.template.base import (
    TemplateCallableType,
    TemplateEngineProtocol,
    TemplateProtocol,
    csrf_token,
    url_for,
)

try:
    from minijinja import Environment
    from minijinja import TemplateError as MiniJinjaTemplateNotFound
except ImportError as e:
    raise MissingDependencyException("minijinja") from e

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    C = TypeVar("C", bound="Callable")

    def pass_state(func: C) -> C: ...

else:
    from minijinja import pass_state

__all__ = (
    "MiniJinjaTemplateEngine",
    "StateProtocol",
)

P = ParamSpec("P")
T = TypeVar("T")


class StateProtocol(Protocol):
    auto_escape: str | None
    current_block: str | None
    env: Environment
    name: str

    def lookup(self, key: str) -> Any | None: ...


def _transform_state(func: TemplateCallableType[Mapping[str, Any], P, T]) -> TemplateCallableType[StateProtocol, P, T]:
    """Transform a template callable to receive a ``StateProtocol`` instance as first argument.

    This is for wrapping callables like ``url_for()`` that receive a mapping as first argument so they can be used
    with minijinja which passes a ``StateProtocol`` instance as first argument.
    """
    pass


class MiniJinjaTemplate(TemplateProtocol):
    """Initialize a template.

    Args:
        template: Base ``MiniJinjaTemplate`` used by the underlying minijinja engine
    """

    def __init__(self, engine: Environment, template_name: str) -> None:
        super().__init__()
        self.engine = engine
        self.template_name = template_name

    def render(self, *args: Any, **kwargs: Any) -> str:
        """Render a template.

        Args:
            args: Positional arguments passed to the engines ``render`` function
            kwargs: Keyword arguments passed to the engines ``render`` function

        Returns:
            Rendered template as a string
        """
        try:
            return str(self.engine.render_template(self.template_name, *args, **kwargs))
        except MiniJinjaTemplateNotFound as err:
            raise TemplateNotFoundException(template_name=self.template_name) from err


class MiniJinjaTemplateEngine(TemplateEngineProtocol["MiniJinjaTemplate", StateProtocol]):
    """The engine instance."""

    def __init__(self, directory: Path | list[Path] | None = None, engine_instance: Environment | None = None) -> None:
        """Minijinja based TemplateEngine.

        Args:
            directory: Direct path or list of directory paths from which to serve templates.
            engine_instance: A Minijinja Environment instance.
        """
        if directory and engine_instance:
            raise ImproperlyConfiguredException(
                "You must provide either a directory or a minijinja Environment instance."
            )
        if directory:

            def _loader(name: str) -> str:
                """Load a template from a directory.

                Args:
                    name: The name of the template

                Returns:
                    The template as a string

                Raises:
                    TemplateNotFoundException: if no template is found.
                """
                pass

            self.engine = Environment(loader=_loader)
        elif engine_instance:
            self.engine = engine_instance
        else:
            raise ImproperlyConfiguredException(
                "You must provide either a directory or a minijinja Environment instance."
            )

        self.register_template_callable("url_for", _transform_state(url_for))
        self.register_template_callable("csrf_token", _transform_state(csrf_token))

    def get_template(self, template_name: str) -> MiniJinjaTemplate:
        """Retrieve a template by matching its name (dotted path) with files in the directory or directories provided.

        Args:
            template_name: A dotted path

        Returns:
            MiniJinjaTemplate instance

        Raises:
            TemplateNotFoundException: if no template is found.
        """
        return MiniJinjaTemplate(self.engine, template_name)

    def register_template_callable(
        self,
        key: str,
        template_callable: TemplateCallableType[StateProtocol, P, T],
    ) -> None:
        """Register a callable on the template engine.

        Args:
            key: The callable key, i.e. the value to use inside the template to call the callable.
            template_callable: A callable to register.

        Returns:
            None
        """
        pass

    def render_string(self, template_string: str, context: Mapping[str, Any]) -> str:
        """Render a template from a string with the given context.

        Args:
            template_string: The template string to render.
            context: A dictionary of variables to pass to the template.

        Returns:
            The rendered template as a string.
        """
        return self.engine.render_str(template_string, **context)

    @classmethod
    def from_environment(cls, minijinja_environment: Environment) -> MiniJinjaTemplateEngine:
        """Create a MiniJinjaTemplateEngine from an existing minijinja Environment instance.

        Args:
            minijinja_environment (Environment): A minijinja Environment instance.

        Returns:
            MiniJinjaTemplateEngine instance
        """
        return cls(directory=None, engine_instance=minijinja_environment)
