from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_add_project: Callable,
        on_save: Callable,
        on_add_key: Callable,
        on_add_group: Callable,
        on_theme_toggle: Callable,
        **kwargs,
    ):
        super().__init__(
            master, height=52, corner_radius=0,
            fg_color=("gray90", "gray18"), **kwargs
        )
        self.grid_propagate(False)

        self._on_save = on_save
        self._on_add_key = on_add_key
        self._on_add_group = on_add_group
        self._on_add_project = on_add_project
        self._on_theme_toggle = on_theme_toggle

        self._context_var = ctk.StringVar(value="")
        self._save_btn: ctk.CTkButton | None = None

        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        # ── Left: app title + breadcrumb ──────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, padx=(16, 0), pady=0, sticky="ns")

        ctk.CTkLabel(
            left,
            text="LocaleInterface",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            left,
            textvariable=self._context_var,
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray55"),
        ).pack(side="left")

        # ── Right: action buttons ─────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=2, padx=(0, 14), pady=0, sticky="ns")

        self._save_btn = ctk.CTkButton(
            right,
            text="Save",
            width=72,
            state="disabled",
            fg_color=("gray78", "gray32"),
            hover_color=("gray70", "gray38"),
            command=self._on_save,
        )
        self._save_btn.pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="+ Key", width=72, command=self._on_add_key
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="+ Group", width=80, command=self._on_add_group
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="+ Project", width=88, command=self._on_add_project
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right,
            text="☀/🌙",
            width=44,
            fg_color="transparent",
            hover_color=("gray80", "gray28"),
            text_color=("gray35", "gray65"),
            command=self._on_theme_toggle,
        ).pack(side="left", padx=(8, 0))

    def set_context(self, project_name: str | None, group: str | None) -> None:
        if project_name and group:
            self._context_var.set(f"{project_name}  ›  {group}")
        elif project_name:
            self._context_var.set(project_name)
        else:
            self._context_var.set("")

    def set_dirty(self, dirty: bool) -> None:
        if self._save_btn is None:
            return
        if dirty:
            self._save_btn.configure(
                state="normal",
                text="Save ●",
                fg_color=("#E07B00", "#C96A00"),
                hover_color=("#C96A00", "#B05A00"),
            )
        else:
            self._save_btn.configure(
                state="disabled",
                text="Save",
                fg_color=("gray78", "gray32"),
                hover_color=("gray70", "gray38"),
            )
