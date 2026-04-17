from __future__ import annotations

import dataclasses
from dataclasses import replace
from typing import TYPE_CHECKING, Generic, TypeVar

import msgspec.inspect
from msgspec import NODEFAULT, Struct, structs

from litestar.dto.base_dto import AbstractDTO
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.dto.field import DTO_FIELD_META_KEY, DTOField, extract_dto_field
from litestar.plugins.core._msgspec import kwarg_definition_from_field
from litestar.types.empty import Empty

if TYPE_CHECKING:
    from collections.abc import Collection, Generator
    from typing import Any

    from litestar.typing import FieldDefinition


__all__ = ("MsgspecDTO",)

T = TypeVar("T", bound="Struct | Collection[Struct]")


def _default_or_empty(value: Any) -> Any:
    pass


def _default_or_none(value: Any) -> Any:
    pass


class MsgspecDTO(AbstractDTO[T], Generic[T]):
    """Support for domain modelling with Msgspec."""

    @classmethod
    def generate_field_definitions(cls, model_type: type[Struct]) -> Generator[DTOFieldDefinition, None, None]:
        pass

    @classmethod
    def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
        pass
