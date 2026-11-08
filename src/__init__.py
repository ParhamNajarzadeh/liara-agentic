"""Liara Agentic SRE Assistant Root Package (`src/__init__.py`).

Provides universal Pydantic v1 (`1.10.x`) and v2 (`2.x`) compatibility shims so that
`model_dump()` and `model_validate()` work identically across all Python environments.
"""

from typing import Any
from pydantic import BaseModel

__version__ = "1.0.0"

if not hasattr(BaseModel, "model_dump"):
    def _model_dump(self: BaseModel, **kwargs: Any) -> Any:
        return self.dict(**kwargs)

    BaseModel.model_dump = _model_dump  # type: ignore[attr-defined]

if not hasattr(BaseModel, "model_validate"):
    @classmethod  # type: ignore[misc]
    def _model_validate(cls: Any, obj: Any) -> Any:
        return cls.parse_obj(obj)

    BaseModel.model_validate = _model_validate  # type: ignore[attr-defined]
