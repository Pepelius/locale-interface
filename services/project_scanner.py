from __future__ import annotations

import os
from pathlib import Path

from models.project import LocaleFile
from utils.locale_detector import is_locale_code, detect_language_from_filename

_LOCALE_FOLDERS = {"locales", "i18n", "translations", "lang", "locale", "strings", "l10n"}
_EXTENSIONS = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".properties": "properties",
    ".po": "po",
}
# These filenames are always included when found in a locale-like folder,
# even if the stem doesn't look like a locale code.
_COMMON_I18N_NAMES = {
    "i18n", "translations", "messages", "strings", "locale",
    "locales", "lang", "dictionary", "copy", "content",
}
_IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".idea", "dist", "build", ".next", "target", ".cache",
}


def scan_for_locale_files(project_path: Path) -> list[LocaleFile]:
    """Walk project_path and return candidate LocaleFile entries.

    Detection heuristics:
    - File is inside a locale-named folder (i18n, locales, …)
    - File stem matches a locale code pattern (en, fi, en_US, …)
    - Parent directory is itself a locale code (i18n/en/messages.json)
    - File extension is a supported format
    """
    candidates: list[LocaleFile] = []
    seen: set[Path] = set()

    for root, dirs, files in os.walk(project_path):
        dirs[:] = sorted(d for d in dirs if d not in _IGNORE_DIRS)

        root_path = Path(root)
        try:
            rel_parts = root_path.relative_to(project_path).parts
        except ValueError:
            continue

        in_locale_folder = any(p.lower() in _LOCALE_FOLDERS for p in rel_parts)

        # Check if any ancestor directory is a locale code (e.g. i18n/en/)
        parent_lang: str | None = None
        for part in rel_parts:
            if is_locale_code(part):
                parent_lang = part
                break

        for fname in files:
            fpath = root_path / fname
            if fpath in seen:
                continue

            suffix = fpath.suffix.lower()
            if suffix not in _EXTENSIONS:
                continue

            fmt = _EXTENSIONS[suffix]
            stem = fpath.stem
            lang = detect_language_from_filename(stem) or parent_lang

            # Include well-known i18n filenames even without a detectable lang code
            is_common_name = stem.lower() in _COMMON_I18N_NAMES

            if lang is None and not in_locale_folder and not is_common_name:
                continue
            if lang is None:
                lang = stem if not is_common_name else ""

            candidates.append(LocaleFile(language=lang, path=fpath, format=fmt))
            seen.add(fpath)

    candidates.sort(key=lambda lf: lf.language)
    return candidates
