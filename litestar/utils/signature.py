from __future__ import annotations

import sys
import typing
from dataclasses import dataclass, replace
from inspect import Signature, getmembers, isclass, ismethod
from itertools import chain
from typing import TYPE_CHECKING, Annotated, Any, Self, Union, get_args, get_origin, get_type_hints

from litestar import connection, datastructures, types
from litestar.types import Empty
from litestar.typing import FieldDefinition
from litestar.utils.typing import expand_type_var_in_type_hint, unwrap_annotation
from litestar.utils.warnings import warn_signature_namespace_override

if TYPE_CHECKING:
    from collections.abc import Sequence

    from litestar.types import AnyCallable


__all__ = (
    "ParsedSignature",
    "add_types_to_signature_namespace",
    "get_fn_type_hints",
    "merge_signature_namespaces",
)

_GLOBAL_NAMES = {
    namespace: export
    for namespace, export in chain(
        tuple(getmembers(types)), tuple(getmembers(connection)), tuple(getmembers(datastructures))
    )
    if namespace[0].isupper() and namespace in chain(types.__all__, connection.__all__, datastructures.__all__)
}
"""A mapping of names used for handler signature forward-ref resolution.

This allows users to include these names within an `if TYPE_CHECKING:` block in their handler module.
"""


def _unwrap_implicit_optional_hints(defaults: dict[str, Any], hints: dict[str, Any]) -> dict[str, Any]:
    """Unwrap implicit optional hints.

    On Python<3.11, if a function parameter annotation has a ``None`` default, it is unconditionally wrapped in an
    ``Optional`` type.

    If the annotation is not annotated, then any nested unions are flattened, e.g.,:

    .. code-block:: python

        def foo(a: Optional[Union[str, int]] = None): ...

    ...will become `Union[str, int, NoneType]`.

    However, if the annotation is annotated, then we end up with an optional union around the annotated type, e.g.,:

    .. code-block:: python

        def foo(a: Annotated[Optional[Union[str, int]], ...] = None): ...

    ... becomes `Union[Annotated[Union[str, int, NoneType], ...], NoneType]`

    This function makes the latter case consistent with the former by either removing the outer union if it is redundant
    or flattening the union if it is not. The latter case would become `Annotated[Union[str, int, NoneType], ...]`.

    Args:
        defaults: Mapping of names to default values.
        hints: Mapping of names to types.

    Returns:
        Mapping of names to types.
    """
    pass


def get_fn_type_hints(fn: Any, namespace: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve type hints for ``fn``.

    Args:
        fn: Callable that is being inspected
        namespace: Extra names for resolution of forward references.

    Returns:
        Mapping of names to types.
    """
    fn_to_inspect: Any = fn

    module_name = fn_to_inspect.__module__

    if isclass(fn_to_inspect):
        fn_to_inspect = fn_to_inspect.__init__

    # detect objects that are not functions and that have a `__call__` method
    if callable(fn_to_inspect) and ismethod(fn_to_inspect.__call__):
        fn_to_inspect = fn_to_inspect.__call__

    # inspect the underlying function for methods
    if hasattr(fn_to_inspect, "__func__"):
        fn_to_inspect = fn_to_inspect.__func__  # pyright: ignore[reportFunctionMemberAccess]
    # Order important. If a litestar name has been overridden in the function module, we want
    # to use that instead of the litestar one.
    namespace = {
        **_GLOBAL_NAMES,
        **vars(typing),
        **vars(sys.modules[module_name]),
        **(namespace or {}),
    }
    hints = get_type_hints(fn_to_inspect, globalns=namespace, include_extras=True)

    return hints


@dataclass(frozen=True)
class ParsedSignature:
    """Parsed signature.

    This object is the primary source of handler/dependency signature information.

    The only post-processing that occurs is the conversion of any forward referenced type annotations.
    """

    __slots__ = ("original_signature", "parameters", "return_type")

    parameters: dict[str, FieldDefinition]
    """A mapping of parameter names to ParsedSignatureParameter instances."""
    return_type: FieldDefinition
    """The return annotation of the callable."""
    original_signature: Signature
    """The raw signature as returned by :func:`inspect.signature`"""

    @classmethod
    def from_fn(cls, fn: AnyCallable, signature_namespace: dict[str, Any]) -> Self:
        """Parse a function signature.

        Args:
            fn: Any callable.
            signature_namespace: mapping of names to types for forward reference resolution

        Returns:
            ParsedSignature
        """
        pass

    @classmethod
    def from_signature(cls, signature: Signature, fn_type_hints: dict[str, type]) -> Self:
        """Parse an :class:`inspect.Signature` instance.

        Args:
            signature: An :class:`inspect.Signature` instance.
            fn_type_hints: mapping of types

        Returns:
            ParsedSignature
        """
        pass


def add_types_to_signature_namespace(
    signature_types: Sequence[Any], signature_namespace: dict[str, Any]
) -> dict[str, Any]:
    """Add types to ith signature namespace mapping.

    Types are added mapped to their `__name__` attribute.

    Args:
        signature_types: A list of types to add to the signature namespace.
        signature_namespace: The signature namespace to add types to.

    Raises:
        AttributeError: If a type does not have a `__name__` attribute.

    Returns:
        The updated signature namespace.
    """
    return merge_signature_namespaces(
        signature_namespace=signature_namespace,
        additional_signature_namespace={signature_type.__name__: signature_type for signature_type in signature_types},
    )


def merge_signature_namespaces(
    signature_namespace: dict[str, Any], additional_signature_namespace: dict[str, Any]
) -> dict[str, Any]:
    """Add types to ith signature namespace mapping.

    Types are added mapped to their `__name__` attribute.

    Args:
        signature_namespace: The signature namespace to add types to.
        additional_signature_namespace: The signature namespace to merge

    Raises:
        AttributeError: If a type does not have a `__name__` attribute.

    Returns:
        The updated signature namespace.
    """
    for signature_key, signature_type in additional_signature_namespace.items():
        if signature_key in signature_namespace and signature_namespace.get(signature_key) != signature_type:
            warn_signature_namespace_override(signature_key)
    signature_namespace.update(additional_signature_namespace)
    return signature_namespace
