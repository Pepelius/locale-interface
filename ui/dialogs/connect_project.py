from __future__ import annotations

import tkinter.filedialog as fd
from pathlib import Path
from typing import Callable

import customtkinter as ctk

from models.project import Project, LocaleFile
from services.project_scanner import scan_for_locale_files

_FORMAT_COLOURS = {
    "json":       ("#3B82F6", "#2563EB"),
    "yaml":       ("#8B5CF6", "#7C3AED"),
    "properties": ("#F59E0B", "#D97706"),
    "po":         ("#10B981", "#059669"),
    "ts":         ("#06B6D4", "#0891B2"),
}


class _FileRow:
    """One row in the file list — checkbox, language entry, path, format badge."""

    def __init__(self, parent: ctk.CTkScrollableFrame, locale_file: LocaleFile,
                 base_path: Path | None):
        self.locale_file = locale_file

        self.enabled_var = ctk.BooleanVar(value=True)
        self.lang_var = ctk.StringVar(value=locale_file.language)

        frame = ctk.CTkFrame(parent, fg_color=("gray88", "gray18"), corner_radius=6)
        frame.pack(fill="x", padx=2, pady=3)
        frame.grid_columnconfigure(2, weight=1)

        ctk.CTkCheckBox(
            frame, text="", variable=self.enabled_var, width=24,
            checkbox_width=18, checkbox_height=18,
        ).grid(row=0, column=0, padx=(8, 4), pady=8, sticky="w")

        lang_entry = ctk.CTkEntry(
            frame, textvariable=self.lang_var,
            width=52, height=28,
            placeholder_text="lang",
            font=ctk.CTkFont(size=12, family="Courier"),
        )
        lang_entry.grid(row=0, column=1, padx=(0, 8), pady=8)

        try:
            rel = locale_file.path.relative_to(base_path) if base_path else locale_file.path
        except ValueError:
            rel = locale_file.path
        ctk.CTkLabel(
            frame, text=str(rel), anchor="w",
            font=ctk.CTkFont(size=12), text_color=("gray20", "gray80"),
        ).grid(row=0, column=2, padx=(0, 8), sticky="ew")

        fg, _ = _FORMAT_COLOURS.get(locale_file.format, ("gray60", "gray50"))
        ctk.CTkLabel(
            frame, text=locale_file.format.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="white", fg_color=fg,
            corner_radius=4, width=44, height=20,
        ).grid(row=0, column=3, padx=(0, 10), pady=8)

    def get_locale_file(self) -> LocaleFile | None:
        if not self.enabled_var.get():
            return None
        lang = self.lang_var.get().strip()
        if not lang:
            return None
        return LocaleFile(language=lang, path=self.locale_file.path, format=self.locale_file.format)


class ConnectProjectDialog(ctk.CTkToplevel):
    def __init__(self, master, on_confirm: Callable[[Project], None]):
        super().__init__(master)
        self.title("Connect Project")
        self.geometry("600x720")
        self.resizable(False, True)
        self._on_confirm = on_confirm

        self._project_path: Path | None = None
        self._locales_path: Path | None = None
        self._file_rows: list[_FileRow] = []
        self._default_lang_var = ctk.StringVar(value="")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)

        # ── Project folder ────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Project folder", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="ew")

        proj_row = ctk.CTkFrame(self, fg_color="transparent")
        proj_row.grid(row=1, column=0, padx=20, sticky="ew")
        proj_row.grid_columnconfigure(0, weight=1)

        self._proj_path_var = ctk.StringVar(value="No folder selected")
        ctk.CTkLabel(
            proj_row, textvariable=self._proj_path_var, anchor="w",
            text_color=("gray50", "gray55"), font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            proj_row, text="Browse…", width=90, height=32,
            command=self._browse_project,
        ).grid(row=0, column=1, padx=(8, 0))

        # ── Project name ──────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Project name", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=2, column=0, padx=20, pady=(14, 4), sticky="ew")

        self._name_entry = ctk.CTkEntry(self, placeholder_text="My Project", height=34)
        self._name_entry.grid(row=3, column=0, padx=20, sticky="ew")

        # ── Locales directory ─────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Locales directory", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=4, column=0, padx=20, pady=(14, 4), sticky="ew")

        locales_row = ctk.CTkFrame(self, fg_color="transparent")
        locales_row.grid(row=5, column=0, padx=20, sticky="ew")
        locales_row.grid_columnconfigure(0, weight=1)

        self._locales_path_var = ctk.StringVar(value="Same as project folder")
        ctk.CTkLabel(
            locales_row, textvariable=self._locales_path_var, anchor="w",
            text_color=("gray50", "gray55"), font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            locales_row, text="Browse…", width=90, height=32,
            command=self._browse_locales,
        ).grid(row=0, column=1, padx=(8, 0))

        # ── Files header ──────────────────────────────────────────────────
        files_header = ctk.CTkFrame(self, fg_color="transparent")
        files_header.grid(row=6, column=0, padx=20, pady=(16, 4), sticky="ew")
        files_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            files_header, text="Locale files", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            files_header, text="+ Add file manually", width=140, height=28,
            fg_color="transparent", border_width=1,
            font=ctk.CTkFont(size=12), command=self._add_manual,
        ).grid(row=0, column=1)

        # ── Files list ────────────────────────────────────────────────────
        self._files_frame = ctk.CTkScrollableFrame(self, height=200)
        self._files_frame.grid(row=8, column=0, padx=20, sticky="nsew", pady=(0, 4))
        self._files_frame.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            self._files_frame,
            text="Select a project folder to scan for locale files.",
            text_color=("gray55", "gray55"), font=ctk.CTkFont(size=12),
            justify="center", wraplength=480,
        )
        self._status_label.pack(pady=24)

        # ── Default locale ────────────────────────────────────────────────
        self._default_row = ctk.CTkFrame(self, fg_color="transparent")
        self._default_row.grid(row=9, column=0, padx=20, pady=(8, 0), sticky="ew")
        self._default_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._default_row, text="Default locale", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self._default_menu = ctk.CTkOptionMenu(
            self._default_row,
            variable=self._default_lang_var,
            values=["—"],
            width=120, height=30,
        )
        self._default_menu.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            self._default_row,
            text="Used as reference when adding new locales.",
            text_color=("gray55", "gray50"), font=ctk.CTkFont(size=11),
        ).grid(row=0, column=2, padx=(10, 0), sticky="w")

        # ── Hint ──────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Edit the language codes in the text fields (e.g. en, fi, de).",
            text_color=("gray55", "gray50"), font=ctk.CTkFont(size=11), anchor="w",
        ).grid(row=10, column=0, padx=22, pady=(8, 0), sticky="w")

        # ── Buttons ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=11, column=0, padx=20, pady=14, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Cancel", width=84, height=34,
            fg_color="transparent", border_width=1, command=self.destroy,
        ).pack(side="left", padx=4)
        self._confirm_btn = ctk.CTkButton(
            btn_frame, text="Connect", width=100, height=34,
            state="disabled", command=self._confirm,
        )
        self._confirm_btn.pack(side="left")

        self.bind("<Escape>", lambda _: self.destroy())

    # ── Browse actions ────────────────────────────────────────────────────

    def _browse_project(self) -> None:
        path_str = fd.askdirectory(parent=self, title="Select Project Folder")
        if not path_str:
            return
        self._project_path = Path(path_str)
        self._proj_path_var.set(str(self._project_path))
        if not self._name_entry.get():
            self._name_entry.insert(0, self._project_path.name)
        # Reset locales path to project path
        self._locales_path = None
        self._locales_path_var.set("Same as project folder")
        self._scan_and_display()

    def _browse_locales(self) -> None:
        initial = str(self._project_path or Path.home())
        path_str = fd.askdirectory(parent=self, title="Select Locales Directory", initialdir=initial)
        if not path_str:
            return
        self._locales_path = Path(path_str)
        try:
            rel = self._locales_path.relative_to(self._project_path) if self._project_path else self._locales_path
            self._locales_path_var.set(str(rel))
        except ValueError:
            self._locales_path_var.set(str(self._locales_path))
        self._scan_and_display()

    def _effective_scan_path(self) -> Path | None:
        return self._locales_path or self._project_path

    def _scan_and_display(self) -> None:
        scan_path = self._effective_scan_path()
        if not scan_path:
            return

        for w in self._files_frame.winfo_children():
            w.destroy()
        self._file_rows.clear()

        candidates = scan_for_locale_files(scan_path)

        if not candidates:
            ctk.CTkLabel(
                self._files_frame,
                text="No locale files detected automatically.\n"
                     "Use '+ Add file manually' to locate your files.",
                text_color=("gray55", "gray55"), font=ctk.CTkFont(size=12),
                justify="center", wraplength=480,
            ).pack(pady=24)
        else:
            for lf in candidates:
                row = _FileRow(self._files_frame, lf, scan_path)
                self._file_rows.append(row)

        self._update_default_locale_menu()
        self._confirm_btn.configure(state="normal")

    def _update_default_locale_menu(self) -> None:
        """Rebuild the Default Locale dropdown from the current file rows."""
        langs = [
            lf.get_locale_file().language
            for lf in self._file_rows
            if lf.get_locale_file() and lf.get_locale_file().language
        ]
        if langs:
            self._default_menu.configure(values=langs)
            if self._default_lang_var.get() not in langs:
                self._default_lang_var.set(langs[0])
        else:
            self._default_menu.configure(values=["—"])
            self._default_lang_var.set("—")

    def _add_manual(self) -> None:
        scan_path = self._effective_scan_path()
        initial_dir = str(scan_path) if scan_path else str(Path.home())

        filetypes = [
            ("All supported", "*.json *.yaml *.yml *.properties *.po *.ts *.tsx *.js"),
            ("JSON", "*.json"),
            ("YAML", "*.yaml *.yml"),
            ("TypeScript / JavaScript", "*.ts *.tsx *.js"),
            ("Properties", "*.properties"),
            ("PO / Gettext", "*.po"),
            ("All files", "*"),
        ]
        path_str = fd.askopenfilename(
            parent=self, title="Select Locale File",
            initialdir=initial_dir, filetypes=filetypes,
        )
        if not path_str:
            return

        file_path = Path(path_str)
        suffix = file_path.suffix.lower()
        fmt_map = {
            ".json": "json", ".yaml": "yaml", ".yml": "yaml",
            ".properties": "properties", ".po": "po",
            ".ts": "ts", ".tsx": "ts", ".js": "ts",
        }
        fmt = fmt_map.get(suffix, "json")

        if not self._file_rows:
            for w in self._files_frame.winfo_children():
                w.destroy()

        from utils.locale_detector import detect_language_from_filename
        lang = detect_language_from_filename(file_path.stem) or ""

        lf = LocaleFile(language=lang, path=file_path, format=fmt)
        row = _FileRow(self._files_frame, lf, scan_path)
        self._file_rows.append(row)
        self._update_default_locale_menu()
        self._confirm_btn.configure(state="normal")

    def _confirm(self) -> None:
        name = self._name_entry.get().strip() or (
            self._project_path.name if self._project_path else "Project"
        )
        selected_files = [
            lf for row in self._file_rows
            if (lf := row.get_locale_file()) is not None
        ]
        default_lang = self._default_lang_var.get()
        if default_lang == "—":
            default_lang = selected_files[0].language if selected_files else ""

        project = Project(
            name=name,
            path=self._project_path or Path("."),
            locale_files=selected_files,
            locales_path=self._locales_path,
            default_language=default_lang,
        )
        self.destroy()
        self._on_confirm(project)

