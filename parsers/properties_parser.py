from __future__ import annotations

from pathlib import Path

from .base import BaseParser


class PropertiesParser(BaseParser):
    def load(self, path: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "!")):
                continue
            for sep in ("=", ":"):
                if sep in line:
                    k, _, v = line.partition(sep)
                    result[k.strip()] = v.strip()
                    break
        return result

    def save(self, path: Path, data: dict[str, str]) -> None:
        lines = [f"{k}={v}" for k, v in sorted(data.items())]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
