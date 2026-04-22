from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LocaleFile:
    language: str        # e.g. "en", "fi", "en_US"
    path: Path
    format: str          # "json" | "yaml" | "properties" | "po" | "ts"


@dataclass
class Project:
    name: str
    path: Path
    locale_files: list[LocaleFile] = field(default_factory=list)
    # Directory that contains the locale files (may differ from project root)
    locales_path: Path | None = None
    # Language code of the reference locale used when creating new locales
    default_language: str = ""

    @property
    def languages(self) -> list[str]:
        return [lf.language for lf in self.locale_files]

    def file_for_language(self, lang: str) -> LocaleFile | None:
        return next((lf for lf in self.locale_files if lf.language == lang), None)

    @property
    def effective_locales_path(self) -> Path:
        """Return the locales directory, falling back to the project root."""
        return self.locales_path or self.path
