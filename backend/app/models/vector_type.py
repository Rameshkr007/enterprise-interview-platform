from __future__ import annotations

import json
from typing import Any
from sqlalchemy import TypeDecorator, Text
from sqlalchemy.dialects.postgresql import JSONB, JSON

class CompatibleVector(TypeDecorator):
    """
    Universal Vector column:
    Stores high-dimensional float embeddings seamlessly.
    Works on native PostgreSQL instances even without pre-compiled pgvector.dll,
    while maintaining full array/list serialization.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 3072, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.dimensions = dimensions

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return list(value)
