from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LocaleString:
    key: str                                    # full dotted path, e.g. "auth.login.title"
    translations: dict[str, str] = field(default_factory=dict)  # lang -> value

    @property
    def group(self) -> str:
        parts = self.key.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    @property
    def short_key(self) -> str:
        return self.key.rsplit(".", 1)[-1]
