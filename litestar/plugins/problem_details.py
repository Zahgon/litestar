"""Plugin for converting exceptions into a problem details response."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

from litestar.exceptions.http_exceptions import HTTPException
from litestar.plugins.base import InitPlugin
from litestar.response.base import Response

if TYPE_CHECKING:
    from litestar.config.app import AppConfig
    from litestar.connection.request import Request
    from litestar.types.callable_types import ExceptionHandler, ExceptionT

ProblemDetailsExceptionT = TypeVar("ProblemDetailsExceptionT", bound="ProblemDetailsException")
ProblemDetailsExceptionHandlerType: TypeAlias = "Callable[[Request, ProblemDetailsExceptionT], Response]"
ExceptionToProblemDetailMapType: TypeAlias = (
    "Mapping[type[ExceptionT], Callable[[ExceptionT], ProblemDetailsExceptionT]]"
)


def _problem_details_exception_handler(request: Request[Any, Any, Any], exc: ProblemDetailsException) -> Response[Any]:
    pass


def _create_exception_handler(
    exc_to_problem_details_exc_fn: Callable[[ExceptionT], ProblemDetailsException], exc_type: type[ExceptionT]
) -> ExceptionHandler[ExceptionT]:
    pass


def _http_exception_to_problem_detail_exception(exc: HTTPException) -> ProblemDetailsException:
    pass


class ProblemDetailsException(HTTPException):
    """A problem details exception as per RFC 9457."""

    _PROBLEM_DETAILS_MEDIA_TYPE = "application/problem+json"

    def __init__(
        self,
        *args: Any,
        detail: str = "",
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | list[Any] | None = None,
        type_: str | None = None,
        title: str | None = None,
        instance: str | None = None,
    ) -> None:
        """Initialize ``ProblemDetailsException``.

        Args:
            *args: if ``detail`` kwarg not provided, first arg should be error detail.
            detail: Exception details or message. Will default to args[0] if not provided.
            status_code: Exception HTTP status code.
            headers: Headers to set on the response.
            extra: An extra mapping to attach to the exception.
            type_: The type field in the problem details.
            title: The title field in the problem details.
            instance: The instance field in the problem details.
        """

        super().__init__(
            *args,
            detail=detail,
            status_code=status_code,
            headers=headers,
            extra=extra,
        )

        self.type_ = type_
        self.title = title
        self.instance = instance

    def to_response(self, request: Request[Any, Any, Any]) -> Response[dict[str, Any]]:
        """Convert the problem details exception into a ``Response.``"""

        problem_details: dict[str, Any] = {"status": self.status_code}
        if self.type_ is not None:
            problem_details["type"] = self.type_
        if self.title is not None:
            problem_details["title"] = self.title
        if self.instance is not None:
            problem_details["instance"] = self.instance
        if self.detail is not None:
            problem_details["detail"] = self.detail

        if extra := self.extra:
            if isinstance(extra, Mapping):
                problem_details.update(extra)
            else:
                problem_details["extra"] = extra

        return Response(
            problem_details,
            headers=self.headers,
            media_type=self._PROBLEM_DETAILS_MEDIA_TYPE,
            status_code=self.status_code,
        )


@dataclass
class ProblemDetailsConfig:
    """The configuration object for ``ProblemDetailsPlugin.``"""

    exception_handler: ProblemDetailsExceptionHandlerType = _problem_details_exception_handler
    """The exception handler used for ``ProblemdetailsException.``"""

    enable_for_all_http_exceptions: bool = False
    """Flag indicating whether to convert all :exc:`HTTPException` into ``ProblemDetailsException.``"""

    exception_to_problem_detail_map: ExceptionToProblemDetailMapType = field(default_factory=dict)
    """A mapping to convert exceptions into ``ProblemDetailsException.``

    All exceptions provided in this will get a custom exception handler where these exceptions
    are converted into ``ProblemDetailException`` before handling them. This can be used to override
    the handler for ``HTTPException`` as well.
    """


class ProblemDetailsPlugin(InitPlugin):
    """A plugin to convert exceptions into problem details as per RFC 9457."""

    def __init__(self, config: ProblemDetailsConfig | None = None):
        self.config = config or ProblemDetailsConfig()

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        pass
