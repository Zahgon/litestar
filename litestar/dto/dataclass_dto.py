from __future__ import annotations

from dataclasses import MISSING, fields, replace
from typing import TYPE_CHECKING, Generic, TypeVar

from litestar.dto.base_dto import AbstractDTO
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.dto.field import DTOField, extract_dto_field
from litestar.params import DependencyKwarg, KwargDefinition
from litestar.types.empty import Empty

if TYPE_CHECKING:
    from collections.abc import Collection, Generator

    from litestar.types.protocols import DataclassProtocol
    from litestar.typing import FieldDefinition


__all__ = ("DataclassDTO", "T")

T = TypeVar("T", bound="DataclassProtocol | Collection[DataclassProtocol]")
AnyDataclass = TypeVar("AnyDataclass", bound="DataclassProtocol")


class DataclassDTO(AbstractDTO[T], Generic[T]):
    """Support for domain modelling with dataclasses."""

    @classmethod
    def generate_field_definitions(
        cls, model_type: type[DataclassProtocol]
    ) -> Generator[DTOFieldDefinition, None, None]:
        pass

    @classmethod
    def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
        pass
