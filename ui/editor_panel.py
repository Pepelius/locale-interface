from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from models.locale_string import LocaleString
from utils.placeholder_utils import validate_consistency

_KEY_COL_W = 200
_LANG_COL_W = 250
_ROW_H = 38
_HEADER_H = 34


class EditorPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_string_changed: Callable[[LocaleString, str, str], None],
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, **kwargs)
        self._on_string_changed = on_string_changed

        self._strings: list[LocaleString] = []
        self._languages: list[str] = []
        self._group: str = ""
        self._view_mode: str = "side_by_side"  # or "single"
        self._active_lang: str = ""

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Top bar ────────────────────────────────────────────────────────
        self._top_bar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        self._top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
        self._top_bar.grid_columnconfigure(1, weight=1)
        self._top_bar.grid_propagate(False)

        self._group_label = ctk.CTkLabel(
            self._top_bar,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self._group_label.grid(row=0, column=0, sticky="w")

        controls = ctk.CTkFrame(self._top_bar, fg_color="transparent")
        controls.grid(row=0, column=2, sticky="e")

        self._view_seg = ctk.CTkSegmentedButton(
            controls,
            values=["Side by side", "Single language"],
            command=self._on_view_seg_change,
            width=240,
        )
        self._view_seg.set("Side by side")
        self._view_seg.pack(side="left", padx=(0, 8))

        self._lang_menu = ctk.CTkOptionMenu(
            controls,
            values=["—"],
            command=self._on_lang_menu_change,
            width=100,
        )
        self._lang_menu.pack(side="left")
        self._lang_menu.configure(state="disabled")

        # ── Scrollable area (header + rows share the same frame) ──────────
        self._rows_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._rows_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 8))

        self._show_empty_state()

    # ── Public API ─────────────────────────────────────────────────────────

    def show_group(
        self,
        strings: list[LocaleString],
        languages: list[str],
        group: str,
    ) -> None:
        self._strings = strings
        self._languages = languages
        self._group = group

        if languages and (not self._active_lang or self._active_lang not in languages):
            self._active_lang = languages[0]

        self._group_label.configure(text=group or "(root)")
        self._lang_menu.configure(
            values=languages if languages else ["—"],
            state="normal" if languages else "disabled",
        )
        if languages:
            self._lang_menu.set(self._active_lang)

        self._rebuild_table()

    def clear(self) -> None:
        self._strings = []
        self._languages = []
        self._group = ""
        self._group_label.configure(text="")
        self._clear_header()
        self._clear_rows()
        self._show_empty_state()

    def set_view_mode(self, mode: str) -> None:
        """mode: 'side_by_side' or 'single'"""
        self._view_mode = mode
        seg_val = "Side by side" if mode == "side_by_side" else "Single language"
        self._view_seg.set(seg_val)
        self._lang_menu.configure(
            state="normal" if mode == "single" and self._languages else "disabled"
        )
        self._rebuild_table()

    # ── Internal ───────────────────────────────────────────────────────────

    def _on_view_seg_change(self, value: str) -> None:
        mode = "side_by_side" if value == "Side by side" else "single"
        self.set_view_mode(mode)

    def _on_lang_menu_change(self, lang: str) -> None:
        self._active_lang = lang
        if self._view_mode == "single":
            self._rebuild_table()

    def _active_languages(self) -> list[str]:
        if self._view_mode == "single":
            return [self._active_lang] if self._active_lang else self._languages[:1]
        return self._languages

    def _rebuild_table(self) -> None:
        self._clear_rows()

        if not self._strings:
            self._show_empty_state()
            return

        langs = self._active_languages()
        self._build_header(langs)
        self._build_rows(langs)

    def _clear_header(self) -> None:
        pass  # header lives inside _rows_frame; cleared by _clear_rows

    def _clear_rows(self) -> None:
        for w in self._rows_frame.winfo_children():
            w.destroy()

    def _show_empty_state(self) -> None:
        container = ctk.CTkFrame(self._rows_frame, fg_color="transparent")
        container.pack(expand=True, pady=60)
        ctk.CTkLabel(
            container,
            text="←  Select a group from the sidebar",
            text_color=("gray55", "gray50"),
            font=ctk.CTkFont(size=14),
            justify="center",
        ).pack()
        ctk.CTkLabel(
            container,
            text="to view and edit its localization strings.",
            text_color=("gray65", "gray45"),
            font=ctk.CTkFont(size=12),
        ).pack(pady=(4, 0))

    def _build_header(self, langs: list[str]) -> None:
        header = ctk.CTkFrame(
            self._rows_frame,
            fg_color=("gray82", "gray22"),
            corner_radius=5,
            height=_HEADER_H,
        )
        header.pack(fill="x", pady=(0, 2))
        header.grid_propagate(False)
        header.grid_columnconfigure(tuple(range(1, len(langs) + 1)), weight=1)

        ctk.CTkLabel(
            header,
            text="KEY",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=_KEY_COL_W,
            anchor="w",
            text_color=("gray45", "gray60"),
        ).grid(row=0, column=0, padx=(12, 0), pady=5, sticky="w")

        for i, lang in enumerate(langs):
            ctk.CTkLabel(
                header,
                text=lang.upper(),
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
                text_color=("gray45", "gray60"),
            ).grid(row=0, column=i + 1, padx=(12, 5), pady=5, sticky="ew")

    def _build_rows(self, langs: list[str]) -> None:
        for idx, string in enumerate(self._strings):
            issues = validate_consistency(string.translations)
            row_bg = ("gray93", "gray17") if idx % 2 == 0 else ("gray96", "gray20")

            row_frame = ctk.CTkFrame(
                self._rows_frame,
                fg_color=row_bg,
                corner_radius=5,
                height=_ROW_H,
            )
            row_frame.pack(fill="x", pady=1)
            row_frame.grid_propagate(False)
            row_frame.grid_columnconfigure(tuple(range(1, len(langs) + 1)), weight=1)

            # Key label + optional warning icon
            key_frame = ctk.CTkFrame(
                row_frame, fg_color="transparent",
                width=_KEY_COL_W,
            )
            key_frame.grid(row=0, column=0, padx=(12, 0), sticky="ns")
            key_frame.grid_propagate(False)

            ctk.CTkLabel(
                key_frame,
                text=string.short_key,
                anchor="w",
                font=ctk.CTkFont(size=12, family="Courier"),
                text_color=("gray20", "gray80"),
                wraplength=_KEY_COL_W - 28,
            ).pack(side="left", fill="y")

            if issues:
                ctk.CTkLabel(
                    key_frame, text="⚠",
                    text_color=("#E07B00", "#FFA040"),
                    font=ctk.CTkFont(size=11),
                ).pack(side="left", padx=2)

            # Translation entries
            for col_i, lang in enumerate(langs):
                value = string.translations.get(lang, "")
                var = ctk.StringVar(value=value)

                has_issue = lang in issues
                entry_border = ("#F59E0B", "#D97706") if has_issue else ("gray75", "gray32")

                entry = ctk.CTkEntry(
                    row_frame,
                    textvariable=var,
                    font=ctk.CTkFont(size=13),
                    border_color=entry_border,
                    border_width=1,
                    height=_ROW_H - 8,
                    corner_radius=4,
                )
                entry.grid(row=0, column=col_i + 1, padx=(8, 5), pady=4, sticky="ew")

                var.trace_add(
                    "write",
                    lambda *_, s=string, l=lang, v=var: self._on_string_changed(s, l, v.get()),
                )

    def _col_configs(self, langs: list[str]) -> list[int]:
        """Return [key_col_width, lang_col_width, ...] adjusted to available space."""
        n = len(langs)
        key_w = _KEY_COL_W
        lang_w = max(160, _LANG_COL_W) if n <= 3 else max(140, _LANG_COL_W - (n - 3) * 30)
        return [key_w] + [lang_w] * n
