from __future__ import annotations

import tkinter.filedialog as fd
from pathlib import Path
from typing import Callable

import customtkinter as ctk

from models.project import Project, LocaleFile
from services.project_scanner import scan_for_locale_files


class ConnectProjectDialog(ctk.CTkToplevel):
    def __init__(self, master, on_confirm: Callable[[Project], None]):
        super().__init__(master)
        self.title("Connect Project")
        self.geometry("540x580")
        self.resizable(False, True)
        self._on_confirm = on_confirm

        self._selected_path: Path | None = None
        self._check_vars: list[tuple[LocaleFile, ctk.BooleanVar]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # ── Folder row ────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Project folder", anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="ew")

        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.grid(row=1, column=0, padx=20, sticky="ew")
        folder_row.grid_columnconfigure(0, weight=1)

        self._path_var = ctk.StringVar(value="No folder selected")
        ctk.CTkLabel(
            folder_row, textvariable=self._path_var, anchor="w",
            text_color=("gray50", "gray55"),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            folder_row, text="Browse…", width=90, command=self._browse,
        ).grid(row=0, column=1, padx=(8, 0))

        # ── Project name ──────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Project name", anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=2, column=0, padx=20, pady=(18, 4), sticky="ew")

        self._name_entry = ctk.CTkEntry(self, placeholder_text="My Project")
        self._name_entry.grid(row=3, column=0, padx=20, sticky="ew")

        # ── Detected files ────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Detected locale files", anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=4, column=0, padx=20, pady=(18, 4), sticky="ew")

        self._files_frame = ctk.CTkScrollableFrame(self, height=180)
        self._files_frame.grid(row=6, column=0, padx=20, sticky="nsew", pady=(0, 4))
        self._files_frame.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._files_frame,
            text="Select a project folder to scan for locale files.",
            text_color=("gray55", "gray55"),
        )
        self._empty_label.pack(pady=20)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=7, column=0, padx=20, pady=16, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Cancel", width=80,
            fg_color="transparent", border_width=1, command=self.destroy,
        ).pack(side="left", padx=4)
        self._confirm_btn = ctk.CTkButton(
            btn_frame, text="Connect", state="disabled", command=self._confirm,
        )
        self._confirm_btn.pack(side="left")

        self.bind("<Escape>", lambda _: self.destroy())

    def _browse(self) -> None:
        path_str = fd.askdirectory(parent=self, title="Select Project Folder")
        if not path_str:
            return
        self._selected_path = Path(path_str)
        self._path_var.set(str(self._selected_path))

        if not self._name_entry.get():
            self._name_entry.insert(0, self._selected_path.name)

        self._scan_and_display()

    def _scan_and_display(self) -> None:
        for w in self._files_frame.winfo_children():
            w.destroy()
        self._check_vars.clear()

        candidates = scan_for_locale_files(self._selected_path)

        if not candidates:
            ctk.CTkLabel(
                self._files_frame,
                text="No locale files detected automatically.\n"
                     "You can still connect the project.",
                text_color=("gray55", "gray55"),
                justify="center",
                wraplength=440,
            ).pack(pady=20)
            self._confirm_btn.configure(state="normal")
            return

        for lf in candidates:
            row = ctk.CTkFrame(self._files_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            var = ctk.BooleanVar(value=True)
            self._check_vars.append((lf, var))
            try:
                rel = lf.path.relative_to(self._selected_path)
            except ValueError:
                rel = lf.path
            ctk.CTkCheckBox(
                row,
                text=f"  [{lf.language}]   {rel}   ({lf.format})",
                variable=var,
            ).pack(side="left", anchor="w", padx=4)

        self._confirm_btn.configure(state="normal")

    def _confirm(self) -> None:
        name = self._name_entry.get().strip() or (
            self._selected_path.name if self._selected_path else "Project"
        )
        selected_files = [lf for lf, var in self._check_vars if var.get()]
        project = Project(
            name=name,
            path=self._selected_path or Path("."),
            locale_files=selected_files,
        )
        self.destroy()
        self._on_confirm(project)
