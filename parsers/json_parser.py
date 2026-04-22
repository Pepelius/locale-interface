from __future__ import annotations

import json
from pathlib import Path

from .base import BaseParser, flatten, unflatten


class JsonParser(BaseParser):
    def load(self, path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8")
        raw = json.loads(text) if text.strip() else {}
        return flatten(raw)

    def save(self, path: Path, data: dict[str, str]) -> None:
        nested = unflatten(data)
        path.write_text(
            json.dumps(nested, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
