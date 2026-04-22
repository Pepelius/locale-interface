from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from models.locale_string import LocaleString
from utils.placeholder_utils import validate_consistency

_KEY_COL_W = 190
_LANG_COL_W = 240
_ROW_H = 36
_HEADER_H = 32


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

        # ── Column headers (non-scrolling) ────────────────────────────────
        self._header_frame = ctk.CTkFrame(
            self, fg_color=("gray82", "gray22"), corner_radius=0, height=_HEADER_H,
        )
        self._header_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(6, 0))
        self._header_frame.grid_propagate(False)

        # ── Scrollable rows ───────────────────────────────────────────────
        self._rows_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._rows_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.grid_rowconfigure(2, weight=1)

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
        self._clear_header()
        self._clear_rows()

        if not self._strings:
            self._show_empty_state()
            return

        langs = self._active_languages()
        self._build_header(langs)
        self._build_rows(langs)

    def _clear_header(self) -> None:
        for w in self._header_frame.winfo_children():
            w.destroy()

    def _clear_rows(self) -> None:
        for w in self._rows_frame.winfo_children():
            w.destroy()

    def _show_empty_state(self) -> None:
        ctk.CTkLabel(
            self._rows_frame,
            text="Select a group from the sidebar to view and edit its strings.",
            text_color=("gray55", "gray50"),
            font=ctk.CTkFont(size=13),
        ).pack(pady=60)

    def _build_header(self, langs: list[str]) -> None:
        col_configs = self._col_configs(langs)

        ctk.CTkLabel(
            self._header_frame,
            text="Key",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=col_configs[0],
            anchor="w",
            text_color=("gray35", "gray65"),
        ).grid(row=0, column=0, padx=(10, 0), pady=4, sticky="w")

        for i, lang in enumerate(langs):
            ctk.CTkLabel(
                self._header_frame,
                text=lang.upper(),
                font=ctk.CTkFont(size=12, weight="bold"),
                width=col_configs[i + 1],
                anchor="w",
                text_color=("gray35", "gray65"),
            ).grid(row=0, column=i + 1, padx=(12, 0), pady=4, sticky="w")

    def _build_rows(self, langs: list[str]) -> None:
        col_configs = self._col_configs(langs)

        for idx, string in enumerate(self._strings):
            issues = validate_consistency(string.translations)
            row_bg = ("gray91", "gray19") if idx % 2 == 0 else "transparent"

            row_frame = ctk.CTkFrame(
                self._rows_frame,
                fg_color=row_bg,
                corner_radius=4,
                height=_ROW_H,
            )
            row_frame.pack(fill="x", pady=1)
            row_frame.grid_propagate(False)
            row_frame.grid_columnconfigure(tuple(range(1, len(langs) + 1)), weight=1)

            # Key label + warning dot if placeholder issues exist
            key_frame = ctk.CTkFrame(
                row_frame, fg_color="transparent",
                width=col_configs[0],
            )
            key_frame.grid(row=0, column=0, padx=(10, 0), sticky="ns")
            key_frame.grid_propagate(False)

            ctk.CTkLabel(
                key_frame,
                text=string.short_key,
                anchor="w",
                font=ctk.CTkFont(size=13, family="Courier"),
                text_color=("gray15", "gray85"),
                wraplength=col_configs[0] - 10,
            ).pack(side="left", fill="y")

            if issues:
                ctk.CTkLabel(
                    key_frame, text="⚠",
                    text_color=("#E07B00", "#FFA040"),
                    font=ctk.CTkFont(size=12),
                ).pack(side="left", padx=2)

            # Translation entries
            for col_i, lang in enumerate(langs):
                value = string.translations.get(lang, "")
                var = ctk.StringVar(value=value)

                has_issue = lang in issues
                entry_border = ("#E07B00", "#FFA040") if has_issue else ("gray70", "gray35")

                entry = ctk.CTkEntry(
                    row_frame,
                    textvariable=var,
                    font=ctk.CTkFont(size=13),
                    border_color=entry_border,
                    height=_ROW_H - 6,
                )
                entry.grid(row=0, column=col_i + 1, padx=(8, 4), pady=3, sticky="ew")

                # Capture string/lang in closure
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
