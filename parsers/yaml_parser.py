from __future__ import annotations

from pathlib import Path

import yaml

from .base import BaseParser, flatten, unflatten


class YamlParser(BaseParser):
    def load(self, path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8")
        raw = yaml.safe_load(text) or {}
        return flatten(raw)

    def save(self, path: Path, data: dict[str, str]) -> None:
        nested = unflatten(data)
        path.write_text(
            yaml.dump(nested, allow_unicode=True, default_flow_style=False, sort_keys=True),
            encoding="utf-8",
        )
