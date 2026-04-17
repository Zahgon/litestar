# pyright: reportUnnecessaryTypeIgnoreComment=false

from __future__ import annotations

import dataclasses
from dataclasses import replace
from typing import TYPE_CHECKING, Annotated, Any, Generic, TypeAlias, TypeVar
from warnings import warn

from typing_extensions import override

from litestar.dto.base_dto import AbstractDTO
from litestar.dto.data_structures import DTOFieldDefinition
from litestar.dto.field import DTO_FIELD_META_KEY, extract_dto_field
from litestar.exceptions import MissingDependencyException, ValidationException
from litestar.plugins.pydantic.utils import get_model_info, is_pydantic_2_model, is_pydantic_undefined
from litestar.types.empty import Empty
from litestar.typing import FieldDefinition

if TYPE_CHECKING:
    from collections.abc import Collection, Generator

    from litestar.dto import DTOConfig

try:
    import pydantic as _  # noqa: F401
except ImportError as e:
    raise MissingDependencyException("pydantic") from e


import pydantic
from pydantic import ValidationError

ModelType: TypeAlias = pydantic.BaseModel


T = TypeVar("T", bound="ModelType | Collection[ModelType]")


__all__ = ("PydanticDTO",)

_down_types: dict[Any, Any] = {
    pydantic.EmailStr: str,
    pydantic.IPvAnyAddress: str,
    pydantic.IPvAnyInterface: str,
    pydantic.IPvAnyNetwork: str,
    pydantic.JsonValue: Any,
    pydantic.AwareDatetime: str,
}


def convert_validation_error(validation_error: ValidationError) -> list[dict[str, Any]]:
    error_list = validation_error.errors()
    for error in error_list:
        if isinstance(exception := error.get("ctx", {}).get("error"), Exception):
            error["ctx"]["error"] = type(exception).__name__  # pyright: ignore[reportTypedDictNotRequiredAccess]
    return error_list  # type: ignore[return-value]


def downtype_for_data_transfer(field_definition: FieldDefinition) -> FieldDefinition:
    pass


class PydanticDTO(AbstractDTO[T], Generic[T]):
    """Support for domain modelling with Pydantic."""

    @override
    def decode_builtins(self, value: dict[str, Any]) -> Any:
        try:
            return super().decode_builtins(value)
        except ValidationError as ex:
            raise ValidationException(extra=convert_validation_error(ex)) from ex

    @override
    def decode_bytes(self, value: bytes) -> Any:
        try:
            return super().decode_bytes(value)
        except ValidationError as ex:
            raise ValidationException(extra=convert_validation_error(ex)) from ex

    @classmethod
    def generate_field_definitions(
        cls,
        model_type: type[pydantic.BaseModel],
    ) -> Generator[DTOFieldDefinition, None, None]:
        pass

    @classmethod
    def detect_nested_field(cls, field_definition: FieldDefinition) -> bool:
        pass

    @classmethod
    def get_config_for_model_type(cls, config: DTOConfig, model_type: type[Any]) -> DTOConfig:
        if (
            is_pydantic_2_model(model_type)
            and (model_config := getattr(model_type, "model_config", None))
            and model_config.get("extra") == "forbid"
        ):
            config = dataclasses.replace(config, forbid_unknown_fields=True)
        return config
