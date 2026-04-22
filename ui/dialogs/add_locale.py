from __future__ import annotations

import tkinter.filedialog as fd
from pathlib import Path
from typing import Callable

import customtkinter as ctk

from models.project import Project

_FORMATS = ["json", "yaml", "properties", "po", "ts"]
_EXT = {"json": ".json", "yaml": ".yaml", "properties": ".properties", "po": ".po", "ts": ".ts"}


class AddLocaleDialog(ctk.CTkToplevel):
    """Dialog for adding a new locale to an existing project.

    On confirm, calls ``on_confirm(lang, file_path, format)``.
    """

    def __init__(
        self,
        master,
        project: Project,
        on_confirm: Callable[[str, Path, str], None],
    ):
        super().__init__(master)
        self.title("Add Locale")
        self.geometry("500x380")
        self.resizable(False, False)
        self._project = project
        self._on_confirm = on_confirm

        self._fmt_var = ctk.StringVar(value=self._detect_project_format())
        self._path_var = ctk.StringVar()

        self.grid_columnconfigure(0, weight=1)

        # ── Language code ─────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Language code", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="ew")

        lang_hint = f"Reference: {project.default_language}" if project.default_language else ""
        ctk.CTkLabel(
            self, text=lang_hint or "e.g. de, sv, fr",
            text_color=("gray55", "gray50"), font=ctk.CTkFont(size=11), anchor="w",
        ).grid(row=1, column=0, padx=20, pady=(0, 4), sticky="ew")

        self._lang_entry = ctk.CTkEntry(
            self, placeholder_text="e.g. de", height=34,
            font=ctk.CTkFont(size=14, family="Courier"),
        )
        self._lang_entry.grid(row=2, column=0, padx=20, sticky="ew")
        self._lang_entry.bind("<KeyRelease>", lambda _: self._refresh_path())

        # ── File format ───────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="File format", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=3, column=0, padx=20, pady=(16, 8), sticky="ew")

        fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        fmt_frame.grid(row=4, column=0, padx=20, sticky="w")
        for i, fmt in enumerate(_FORMATS):
            ctk.CTkRadioButton(
                fmt_frame, text=fmt.upper(), variable=self._fmt_var, value=fmt,
                font=ctk.CTkFont(size=12),
                command=self._refresh_path,
            ).grid(row=0, column=i, padx=(0, 12))

        # ── Output file path ──────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Output file", anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=5, column=0, padx=20, pady=(16, 4), sticky="ew")

        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.grid(row=6, column=0, padx=20, sticky="ew")
        path_row.grid_columnconfigure(0, weight=1)

        ctk.CTkEntry(
            path_row, textvariable=self._path_var,
            height=34, font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            path_row, text="…", width=40, height=34, command=self._browse_path,
        ).grid(row=0, column=1, padx=(6, 0))

        # ── Info label ────────────────────────────────────────────────────
        default_lang = project.default_language
        if default_lang:
            info_text = (
                f"All keys from the '{default_lang}' locale will be copied as initial values.\n"
                "You can edit them afterwards."
            )
        else:
            info_text = "The new file will be created with all keys (values left empty)."
        ctk.CTkLabel(
            self, text=info_text,
            text_color=("gray55", "gray50"), font=ctk.CTkFont(size=11),
            justify="left", wraplength=440, anchor="w",
        ).grid(row=7, column=0, padx=20, pady=(12, 0), sticky="ew")

        # ── Buttons ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=8, column=0, padx=20, pady=20, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Cancel", width=84, height=34,
            fg_color="transparent", border_width=1, command=self.destroy,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_frame, text="Add Locale", width=110, height=34,
            command=self._confirm,
        ).pack(side="left")

        self._refresh_path()
        self._lang_entry.focus()
        self.bind("<Escape>", lambda _: self.destroy())

    # ── Helpers ───────────────────────────────────────────────────────────

    def _detect_project_format(self) -> str:
        """Guess format from existing locale files, default to json."""
        if self._project.locale_files:
            return self._project.locale_files[0].format
        return "json"

    def _refresh_path(self) -> None:
        """Auto-suggest file path based on lang + format."""
        lang = self._lang_entry.get().strip()
        fmt = self._fmt_var.get()
        ext = _EXT.get(fmt, ".json")
        base = self._project.effective_locales_path
        if lang:
            self._path_var.set(str(base / f"{lang}{ext}"))
        else:
            self._path_var.set(str(base / f"<lang>{ext}"))

    def _browse_path(self) -> None:
        ext = _EXT.get(self._fmt_var.get(), ".json")
        initial = str(self._project.effective_locales_path)
        fmt = self._fmt_var.get()
        filetypes = [
            (f"{fmt.upper()} files", f"*{ext}"),
            ("All files", "*"),
        ]
        path_str = fd.asksaveasfilename(
            parent=self, title="Save Locale File As",
            initialdir=initial,
            defaultextension=ext,
            filetypes=filetypes,
        )
        if path_str:
            self._path_var.set(path_str)

    def _confirm(self) -> None:
        lang = self._lang_entry.get().strip()
        if not lang:
            self._lang_entry.focus()
            return
        path_str = self._path_var.get().strip()
        if not path_str or "<lang>" in path_str:
            self._lang_entry.focus()
            return
        fmt = self._fmt_var.get()
        file_path = Path(path_str)
        self.destroy()
        self._on_confirm(lang, file_path, fmt)
