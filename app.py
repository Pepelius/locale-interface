from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from models.locale_string import LocaleString
from models.project import Project
from parsers.base import BaseParser
from parsers.json_parser import JsonParser
from parsers.po_parser import PoParser
from parsers.properties_parser import PropertiesParser
from parsers.ts_parser import TypeScriptParser
from parsers.yaml_parser import YamlParser
from services.project_store import load_projects, save_projects
from ui.dialogs.add_group import AddGroupDialog
from ui.dialogs.add_key import AddKeyDialog
from ui.dialogs.add_locale import AddLocaleDialog
from ui.dialogs.connect_project import ConnectProjectDialog
from ui.editor_panel import EditorPanel
from ui.sidebar import Sidebar
from ui.toolbar import Toolbar

_PARSERS: dict[str, BaseParser] = {
    "json": JsonParser(),
    "yaml": YamlParser(),
    "properties": PropertiesParser(),
    "po": PoParser(),
    "ts": TypeScriptParser(),
}


def _get_parser(fmt: str) -> BaseParser:
    return _PARSERS[fmt]


def _load_strings(project: Project) -> list[LocaleString]:
    """Load all locale files for *project* and merge into LocaleString list."""
    merged: dict[str, dict[str, str]] = {}
    for lf in project.locale_files:
        if not lf.path.exists():
            continue
        try:
            flat = _get_parser(lf.format).load(lf.path)
            for key, value in flat.items():
                merged.setdefault(key, {})[lf.language] = value
        except Exception as exc:
            print(f"[LocaleInterface] Could not load {lf.path}: {exc}")

    return [LocaleString(key=k, translations=v) for k, v in sorted(merged.items())]


def _save_strings(project: Project, strings: list[LocaleString]) -> None:
    """Save all in-memory strings back to the original locale files."""
    for lf in project.locale_files:
        flat = {s.key: s.translations.get(lf.language, "") for s in strings}
        try:
            _get_parser(lf.format).save(lf.path, flat)
        except Exception as exc:
            print(f"[LocaleInterface] Could not save {lf.path}: {exc}")


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("LocaleInterface")
        self.geometry("1300x780")
        self.minsize(900, 600)

        # ── App state ──────────────────────────────────────────────────────
        self.projects: list[Project] = load_projects()
        # project_name -> loaded strings
        self._all_strings: dict[str, list[LocaleString]] = {}
        self.current_project: Project | None = None
        self.current_group: str | None = None
        self._dirty = False

        # Eager-load strings for persisted projects
        for p in self.projects:
            self._all_strings[p.name] = _load_strings(p)

        # ── UI ─────────────────────────────────────────────────────────────
        self._build_ui()
        self._refresh_sidebar()

        # Keyboard shortcuts
        self.bind("<Control-s>", lambda _: self._save())
        self.bind("<Command-s>", lambda _: self._save())

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.toolbar = Toolbar(
            self,
            on_add_project=self._open_connect_dialog,
            on_save=self._save,
            on_add_key=self._open_add_key_dialog,
            on_add_group=self._open_add_group_dialog,
            on_theme_toggle=self._toggle_theme,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew")

        # Thin separator below toolbar
        ctk.CTkFrame(self, height=1, corner_radius=0,
                     fg_color=("gray80", "gray25")).grid(row=1, column=0, sticky="ew")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        self.sidebar = Sidebar(
            content,
            on_group_selected=self._on_group_selected,
            on_project_removed=self._on_project_removed,
            on_add_locale=self._open_add_locale_dialog,
            width=264,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.editor = EditorPanel(
            content,
            on_string_changed=self._on_string_changed,
            on_add_key=self._on_key_added_inline,
            on_delete_key=self._on_key_deleted,
        )
        self.editor.grid(row=0, column=1, sticky="nsew")

    # ── Sidebar data ───────────────────────────────────────────────────────

    def _refresh_sidebar(self) -> None:
        data = [
            (p, self._all_strings.get(p.name, []))
            for p in self.projects
        ]
        self.sidebar.set_data(data)
        if self.current_project and self.current_group is not None:
            self.sidebar.set_selected(self.current_project.name, self.current_group)

    # ── Event handlers ─────────────────────────────────────────────────────

    def _on_group_selected(self, project: Project, group: str) -> None:
        if self.current_project != project:
            self.current_project = project
            # Reload strings if not already in memory
            if project.name not in self._all_strings:
                self._all_strings[project.name] = _load_strings(project)

        self.current_group = group
        strings = self._all_strings.get(project.name, [])
        group_strings = [s for s in strings if s.group == group]

        self.editor.show_group(group_strings, project.languages, group)
        self.toolbar.set_context(project.name, group)

    def _on_project_removed(self, project: Project) -> None:
        self.projects = [p for p in self.projects if p.name != project.name]
        self._all_strings.pop(project.name, None)
        if self.current_project and self.current_project.name == project.name:
            self.current_project = None
            self.current_group = None
            self.editor.clear()
            self.toolbar.set_context(None, None)
        save_projects(self.projects)
        self._refresh_sidebar()

    def _on_string_changed(
        self, locale_string: LocaleString, lang: str, value: str,
    ) -> None:
        locale_string.translations[lang] = value
        if not self._dirty:
            self._dirty = True
            self.toolbar.set_dirty(True)

    # ── Save ───────────────────────────────────────────────────────────────

    def _save(self) -> None:
        if not (self.current_project and self._dirty):
            return
        strings = self._all_strings.get(self.current_project.name, [])
        _save_strings(self.current_project, strings)
        self._dirty = False
        self.toolbar.set_dirty(False)

    # ── Add project dialog ─────────────────────────────────────────────────

    def _open_connect_dialog(self) -> None:
        dlg = ConnectProjectDialog(self, on_confirm=self._on_project_connected)
        dlg.grab_set()

    def _on_project_connected(self, project: Project) -> None:
        # Prevent duplicate names
        existing_names = {p.name for p in self.projects}
        name = project.name
        suffix = 1
        while name in existing_names:
            suffix += 1
            name = f"{project.name} ({suffix})"
        project.name = name

        self.projects.append(project)
        self._all_strings[project.name] = _load_strings(project)
        save_projects(self.projects)
        self._refresh_sidebar()

    # ── Add locale dialog ──────────────────────────────────────────────────

    def _open_add_locale_dialog(self, project: Project) -> None:
        dlg = AddLocaleDialog(
            self,
            project=project,
            on_confirm=lambda lang, path, fmt: self._on_locale_added(project, lang, path, fmt),
        )
        dlg.grab_set()

    def _on_locale_added(self, project: Project, lang: str, file_path: Path, fmt: str) -> None:
        from models.project import LocaleFile
        # Build flat dict from the default locale (or empty if no default)
        strings = self._all_strings.get(project.name, [])
        default_lang = project.default_language
        flat: dict[str, str] = {}
        for s in strings:
            flat[s.key] = s.translations.get(default_lang, "") if default_lang else ""

        # Create the new locale file on disk
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            _get_parser(fmt).save(file_path, flat)
        except Exception as exc:
            print(f"[LocaleInterface] Could not create locale file {file_path}: {exc}")
            return

        # Register the new locale file in the project
        new_lf = LocaleFile(language=lang, path=file_path, format=fmt)
        project.locale_files.append(new_lf)

        # Merge the new language into in-memory strings
        for s in strings:
            s.translations.setdefault(lang, flat.get(s.key, ""))

        save_projects(self.projects)
        self._refresh_sidebar()

        # Refresh editor if this project is currently selected
        if self.current_project and self.current_project.name == project.name and self.current_group is not None:
            group_strings = [s for s in strings if s.group == self.current_group]
            self.editor.show_group(group_strings, project.languages, self.current_group)

    # ── Add key dialog ─────────────────────────────────────────────────────

    def _open_add_key_dialog(self) -> None:
        if not self.current_project:
            return
        dlg = AddKeyDialog(
            self,
            group=self.current_group or "",
            languages=self.current_project.languages,
            on_confirm=self._on_key_added,
        )
        dlg.grab_set()

    def _on_key_added(self, key: str, translations: dict[str, str]) -> None:
        if not self.current_project:
            return
        strings = self._all_strings.setdefault(self.current_project.name, [])
        new_str = LocaleString(key=key, translations=translations)
        strings.append(new_str)
        strings.sort(key=lambda s: s.key)

        self._dirty = True
        self.toolbar.set_dirty(True)
        self._refresh_sidebar()

        # Refresh editor if the new key belongs to the current group
        if self.current_group is not None and new_str.group == self.current_group:
            group_strings = [s for s in strings if s.group == self.current_group]
            self.editor.show_group(
                group_strings, self.current_project.languages, self.current_group,
            )

    def _on_key_added_inline(self, key: str, translations: dict[str, str]) -> str | None:
        """Called from the inline add row. Returns an error string or None on success."""
        if not self.current_project:
            return "No project selected."
        strings = self._all_strings.setdefault(self.current_project.name, [])
        if any(s.key == key for s in strings):
            return f'Key "{key}" already exists.'
        new_str = LocaleString(key=key, translations=translations)
        strings.append(new_str)
        strings.sort(key=lambda s: s.key)

        self._dirty = True
        self.toolbar.set_dirty(True)
        self._refresh_sidebar()

        if self.current_group is not None and new_str.group == self.current_group:
            group_strings = [s for s in strings if s.group == self.current_group]
            self.editor.show_group(
                group_strings, self.current_project.languages, self.current_group,
            )
        return None

    def _on_key_deleted(self, string: LocaleString) -> None:
        """Remove a key from all locale files (in-memory + marks dirty)."""
        if not self.current_project:
            return
        strings = self._all_strings.get(self.current_project.name, [])
        self._all_strings[self.current_project.name] = [
            s for s in strings if s.key != string.key
        ]

        self._dirty = True
        self.toolbar.set_dirty(True)
        self._refresh_sidebar()

        if self.current_group is not None:
            updated = self._all_strings[self.current_project.name]
            group_strings = [s for s in updated if s.group == self.current_group]
            self.editor.show_group(
                group_strings, self.current_project.languages, self.current_group,
            )

    # ── Add group dialog ───────────────────────────────────────────────────

    def _open_add_group_dialog(self) -> None:
        if not self.current_project:
            return
        dlg = AddGroupDialog(
            self,
            parent_group=self.current_group or "",
            on_confirm=self._on_group_added,
        )
        dlg.grab_set()

    def _on_group_added(self, group_path: str) -> None:
        """Groups are virtual (derived from key prefixes). Navigate to the new group."""
        if not self.current_project:
            return
        self.current_group = group_path
        strings = self._all_strings.get(self.current_project.name, [])
        group_strings = [s for s in strings if s.group == group_path]
        self.editor.show_group(
            group_strings, self.current_project.languages, group_path,
        )
        self.toolbar.set_context(self.current_project.name, group_path)

    # ── Theme ──────────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if current == "Dark" else "dark")
