from __future__ import annotations

import inspect
from inspect import Signature
from typing import Any

from litestar.plugins import DIPlugin
from litestar.plugins.pydantic.utils import is_pydantic_model_class


class PydanticDIPlugin(DIPlugin):
    def has_typed_init(self, type_: Any) -> bool:
        pass

    def get_typed_init(self, type_: Any) -> tuple[Signature, dict[str, Any]]:
        pass
