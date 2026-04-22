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
            master, height=54, corner_radius=0,
            fg_color=("gray92", "gray15"), **kwargs
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
        left.grid(row=0, column=0, padx=(18, 0), pady=0, sticky="ns")

        ctk.CTkLabel(
            left,
            text="LocaleInterface",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("gray10", "gray95"),
        ).pack(side="left", padx=(0, 6))

        # Separator dot
        ctk.CTkLabel(
            left, text="·",
            font=ctk.CTkFont(size=14),
            text_color=("gray65", "gray45"),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            left,
            textvariable=self._context_var,
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray55"),
        ).pack(side="left")

        # ── Right: action buttons ─────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=2, padx=(0, 16), pady=0, sticky="ns")

        self._save_btn = ctk.CTkButton(
            right,
            text="Save",
            width=76,
            height=32,
            state="disabled",
            fg_color=("gray78", "gray30"),
            hover_color=("gray70", "gray36"),
            text_color=("gray35", "gray60"),
            command=self._on_save,
        )
        self._save_btn.pack(side="left", padx=3)

        # Thin vertical separator
        ctk.CTkFrame(
            right, width=1, height=22,
            fg_color=("gray75", "gray35"),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            right, text="+ Key", width=72, height=32,
            command=self._on_add_key,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="+ Group", width=82, height=32,
            command=self._on_add_group,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right, text="+ Project", width=90, height=32,
            command=self._on_add_project,
        ).pack(side="left", padx=3)

        # Thin vertical separator
        ctk.CTkFrame(
            right, width=1, height=22,
            fg_color=("gray75", "gray35"),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            right,
            text="◑",
            width=34,
            height=32,
            fg_color="transparent",
            hover_color=("gray82", "gray25"),
            text_color=("gray40", "gray65"),
            font=ctk.CTkFont(size=15),
            command=self._on_theme_toggle,
        ).pack(side="left")

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
                text="Save  ●",
                fg_color=("#2563EB", "#1D4ED8"),
                hover_color=("#1D4ED8", "#1E40AF"),
                text_color="white",
            )
        else:
            self._save_btn.configure(
                state="disabled",
                text="Save",
                fg_color=("gray78", "gray30"),
                hover_color=("gray70", "gray36"),
                text_color=("gray35", "gray60"),
            )
