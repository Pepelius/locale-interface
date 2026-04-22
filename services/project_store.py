from __future__ import annotations

import json
from pathlib import Path

from models.project import Project, LocaleFile

_APP_DIR = Path.home() / ".localeinterface"
_STORE_FILE = _APP_DIR / "projects.json"


def load_projects() -> list[Project]:
    if not _STORE_FILE.exists():
        return []
    try:
        raw = json.loads(_STORE_FILE.read_text(encoding="utf-8"))
        projects = []
        for p in raw.get("projects", []):
            files = [
                LocaleFile(
                    language=lf["language"],
                    path=Path(lf["path"]),
                    format=lf["format"],
                )
                for lf in p.get("locale_files", [])
            ]
            lp = p.get("locales_path")
            projects.append(Project(
                name=p["name"],
                path=Path(p["path"]),
                locale_files=files,
                locales_path=Path(lp) if lp else None,
                default_language=p.get("default_language", ""),
            ))
        return projects
    except Exception:
        return []


def save_projects(projects: list[Project]) -> None:
    _APP_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "projects": [
            {
                "name": p.name,
                "path": str(p.path),
                "locales_path": str(p.locales_path) if p.locales_path else None,
                "default_language": p.default_language,
                "locale_files": [
                    {"language": lf.language, "path": str(lf.path), "format": lf.format}
                    for lf in p.locale_files
                ],
            }
            for p in projects
        ]
    }
    _STORE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
