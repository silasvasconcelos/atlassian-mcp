from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class OpenAPILoadError(RuntimeError):
    pass


def load_openapi(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise OpenAPILoadError(
            f"OpenAPI spec not found at {file_path}. "
            "Run scripts/update_openapi.py to download it."
        )
    return json.loads(file_path.read_text(encoding="utf-8"))
