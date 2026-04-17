# pyright: reportUnnecessaryTypeIgnoreComment=false

"""DTO backends do the heavy lifting of decoding and validating raw bytes into domain models, and
back again, to bytes.
"""

from __future__ import annotations

import linecache
import re
import secrets
import textwrap
from collections.abc import Callable, Generator, Mapping
from contextlib import AbstractContextManager, contextmanager, nullcontext
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    cast,
)

from msgspec import UNSET

from litestar.dto._backend import DTOBackend
from litestar.dto._types import (
    CollectionType,
    CompositeType,
    MappingType,
    SimpleType,
    TransferDTOFieldDefinition,
    TransferType,
    UnionType,
)
from litestar.utils.helpers import unique_name_for_scope

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.dto import AbstractDTO
    from litestar.types.serialization import LitestarEncodableType
    from litestar.typing import FieldDefinition

__all__ = ("DTOCodegenBackend",)


class DTOCodegenBackend(DTOBackend):
    __slots__ = (
        "_encode_data",
        "_transfer_to_dict",
        "_transfer_to_model_type",
    )

    def __init__(
        self,
        dto_factory: type[AbstractDTO],
        field_definition: FieldDefinition,
        handler_id: str,
        is_data_field: bool,
        model_type: type[Any],
        wrapper_attribute_name: str | None,
    ) -> None:
        """Create dto backend instance.

        Args:
            dto_factory: The DTO factory class calling this backend.
            field_definition: Parsed type.
            handler_id: The name of the handler that this backend is for.
            is_data_field: Whether the field is a subclass of DTOData.
            model_type: Model type.
            wrapper_attribute_name: If the data that DTO should operate upon is wrapped in a generic datastructure,
              this is the name of the attribute that the data is stored in.
        """
        super().__init__(
            dto_factory=dto_factory,
            field_definition=field_definition,
            handler_id=handler_id,
            is_data_field=is_data_field,
            model_type=model_type,
            wrapper_attribute_name=wrapper_attribute_name,
        )
        self._transfer_to_dict = self._create_transfer_data_fn(
            destination_type=dict,
            field_definition=self.field_definition,
        )
        self._transfer_to_model_type = self._create_transfer_data_fn(
            destination_type=self.model_type,
            field_definition=self.field_definition,
        )
        self._encode_data = self._create_transfer_data_fn(
            destination_type=self.transfer_model_type,
            field_definition=self.field_definition,
        )

    def populate_data_from_builtins(self, builtins: Any, asgi_connection: ASGIConnection) -> Any:
        """Populate model instance from builtin types.

        Args:
            builtins: Builtin type.
            asgi_connection: The current ASGI Connection

        Returns:
            Instance or collection of ``model_type`` instances.
        """
        if self.dto_data_type:
            return self.dto_data_type(
                backend=self,
                data_as_builtins=self._transfer_to_dict(self.parse_builtins(builtins, asgi_connection)),
            )
        return self.transfer_data_from_builtins(self.parse_builtins(builtins, asgi_connection))

    def transfer_data_from_builtins(self, builtins: Any) -> Any:
        """Populate model instance from builtin types.

        Args:
            builtins: Builtin type.

        Returns:
            Instance or collection of ``model_type`` instances.
        """
        return self._transfer_to_model_type(builtins)

    def populate_data_from_raw(self, raw: bytes, asgi_connection: ASGIConnection) -> Any:
        """Parse raw bytes into instance of `model_type`.

        Args:
            raw: bytes
            asgi_connection: The current ASGI Connection

        Returns:
            Instance or collection of ``model_type`` instances.
        """
        if self.dto_data_type:
            return self.dto_data_type(
                backend=self,
                data_as_builtins=self._transfer_to_dict(self.parse_raw(raw, asgi_connection)),
            )
        return self._transfer_to_model_type(self.parse_raw(raw, asgi_connection))

    def encode_data(self, data: Any) -> LitestarEncodableType:
        """Encode data into a ``LitestarEncodableType``.

        Args:
            data: Data to encode.

        Returns:
            Encoded data.
        """
        if self.wrapper_attribute_name:
            wrapped_transfer = self._encode_data(getattr(data, self.wrapper_attribute_name))
            setattr(data, self.wrapper_attribute_name, wrapped_transfer)
            return cast("LitestarEncodableType", data)

        return cast("LitestarEncodableType", self._encode_data(data))

    def _create_transfer_data_fn(
        self,
        destination_type: type[Any],
        field_definition: FieldDefinition,
    ) -> Any:
        """Create instance or iterable of instances of ``destination_type``.

        Args:
            destination_type: the model type received by the DTO on type narrowing.
            field_definition: the parsed type that represents the handler annotation for which the DTO is being applied.

        Returns:
            Data parsed into ``destination_type``.
        """
        pass


class FieldAccessManager(Protocol):
    def __call__(self, source_name: str, field_name: str, expect_optional: bool) -> AbstractContextManager[str]: ...


class TransferFunctionFactory:
    def __init__(
        self,
        is_data_field: bool,
        nested_as_dict: bool,
        attribute_accessor: Callable[[object, str], Any],
    ) -> None:
        self.attribute_accessor = attribute_accessor
        self.is_data_field = is_data_field
        self._fn_locals: dict[str, Any] = {
            "Mapping": Mapping,
            "UNSET": UNSET,
        }
        if attribute_accessor is not getattr:
            self.attribute_accessor_name: str | None = self._add_to_fn_globals("__getattr_impl", attribute_accessor)
        else:
            self.attribute_accessor_name = None
        self._indentation = 1
        self._body = ""
        self.names: set[str] = set()
        self.nested_as_dict = nested_as_dict
        self._re_index_access = re.compile(r"\[['\"](\w+?)['\"]]")

    def _add_to_fn_globals(self, name: str, value: Any) -> str:
        pass

    def _create_local_name(self, name: str) -> str:
        pass

    def _make_function(
        self,
        source_value_name: str,
        return_value_name: str,
        fn_name: str = "func",
    ) -> Callable[[Any], Any]:
        """Wrap the current body contents in a function definition and turn it into a callable object"""
        pass

    def _add_stmt(self, stmt: str) -> None:
        pass

    @contextmanager
    def _start_block(self, expr: str | None = None) -> Generator[None, None, None]:
        """Start an indented block. If `expr` is given, use it as the "opening line"
        of the block.
        """
        pass

    @contextmanager
    def _try_except_pass(self, exception: str) -> Generator[None, None, None]:
        """Enter a `try / except / pass` block. Content written while inside this context
        will go into the `try` block.
        """
        pass

    @contextmanager
    def _access_mapping_item(
        self, source_name: str, field_name: str, expect_optional: bool
    ) -> Generator[str, None, None]:
        """Enter a context within which an item of a mapping can be accessed safely,
        i.e. only if it is contained within that mapping.
        Yields an expression that accesses the mapping item. Content written while
        within this context can use this expression to access the desired value.
        """
        pass

    @contextmanager
    def _access_attribute(self, source_name: str, field_name: str, expect_optional: bool) -> Generator[str, None, None]:
        """Enter a context within which an attribute of an object can be accessed
        safely, i.e. only if the object actually has the attribute.
        Yields an expression that retrieves the object attribute. Content written while
        within this context can use this expression to access the desired value.
        """
        pass

    @classmethod
    def create_transfer_instance_data(
        cls,
        field_definitions: tuple[TransferDTOFieldDefinition, ...],
        destination_type: type[Any],
        is_data_field: bool,
        attribute_accessor: Callable[[object, str], Any],
    ) -> Callable[[Any], Any]:
        pass

    @classmethod
    def create_transfer_type_data(
        cls,
        transfer_type: TransferType,
        is_data_field: bool,
        attribute_accessor: Callable[[object, str], Any],
    ) -> Callable[[Any], Any]:
        pass

    @classmethod
    def create_transfer_data(
        cls,
        *,
        destination_type: type[Any],
        field_definitions: tuple[TransferDTOFieldDefinition, ...],
        is_data_field: bool,
        field_definition: FieldDefinition | None = None,
        attribute_accessor: Callable[[object, str], Any],
    ) -> Callable[[Any], Any]:
        pass

    def _create_transfer_data_body_nested(
        self,
        field_definition: FieldDefinition,
        field_definitions: tuple[TransferDTOFieldDefinition, ...],
        destination_type: type[Any],
        source_data_name: str,
        assignment_target: str,
    ) -> None:
        pass

    def _create_transfer_instance_data(
        self,
        tmp_return_type_name: str,
        source_instance_name: str,
        destination_type_name: str,
        field_definitions: tuple[TransferDTOFieldDefinition, ...],
        destination_type_is_dict: bool,
    ) -> None:
        pass

    def _create_transfer_instance_data_inner(
        self,
        *,
        local_dict_name: str,
        field_definitions: tuple[TransferDTOFieldDefinition, ...],
        access_field_safe: FieldAccessManager,
        source_instance_name: str,
    ) -> None:
        pass

    def _create_transfer_type_data_body(
        self,
        transfer_type: TransferType,
        nested_as_dict: bool,
        source_value_name: str,
        assignment_target: str,
    ) -> None:
        pass

    def _create_transfer_nested_union_type_data(
        self,
        transfer_type: UnionType,
        source_value_name: str,
        assignment_target: str,
    ) -> None:
        pass
