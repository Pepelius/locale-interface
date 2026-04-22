from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


def flatten(d: dict, prefix: str = "") -> dict[str, str]:
    """Recursively flatten a nested dict into {dotted.key: value}."""
    result: dict[str, str] = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, full_key))
        else:
            result[full_key] = str(value) if value is not None else ""
    return result


def unflatten(d: dict[str, str]) -> dict:
    """Reconstruct a nested dict from {dotted.key: value}."""
    result: dict = {}
    for key, value in d.items():
        parts = key.split(".")
        cur = result
        for part in parts[:-1]:
            cur = cur.setdefault(part, {})
        cur[parts[-1]] = value
    return result


class BaseParser(ABC):
    @abstractmethod
    def load(self, path: Path) -> dict[str, str]:
        """Return flat {dotted.key: value} mapping."""

    @abstractmethod
    def save(self, path: Path, data: dict[str, str]) -> None:
        """Write flat mapping back to file in the original format."""
