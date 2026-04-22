from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from models.locale_string import LocaleString
from utils.placeholder_utils import validate_consistency

_KEY_COL_W = 200
_LANG_COL_W = 250
_ROW_H = 38
_HEADER_H = 34
_ACT_COL_W = 40  # delete / confirm button column


class EditorPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_string_changed: Callable[[LocaleString, str, str], None],
        on_add_key: Callable[[str, dict[str, str]], str | None] | None = None,
        on_delete_key: Callable[[LocaleString], None] | None = None,
        on_save: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, **kwargs)
        self._on_string_changed = on_string_changed
        self._on_add_key = on_add_key
        self._on_delete_key = on_delete_key
        self._on_save = on_save

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
        self._group = None
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

        if self._group is None:
            self._show_empty_state()
            return

        langs = self._active_languages()
        if not langs:
            # Group selected but project has no locale files yet
            return

        self._build_header(langs)
        if self._strings:
            self._build_rows(langs)
        self._build_add_row(langs)

    def _clear_header(self) -> None:
        pass  # header lives inside _rows_frame; cleared by _clear_rows

    def _clear_rows(self) -> None:
        for w in self._rows_frame.winfo_children():
            w.destroy()

    def _show_empty_state(self) -> None:
        # Only show when no group is selected at all
        if self._group is not None:
            return
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
        header.grid_columnconfigure(0, minsize=_KEY_COL_W, weight=0)
        header.grid_columnconfigure(tuple(range(1, len(langs) + 1)), weight=1)
        header.grid_columnconfigure(len(langs) + 1, minsize=_ACT_COL_W, weight=0)

        ctk.CTkLabel(
            header,
            text="KEY",
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
            text_color=("gray45", "gray60"),
        ).grid(row=0, column=0, padx=(12, 0), pady=5, sticky="ew")

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
            row_frame.grid_columnconfigure(0, minsize=_KEY_COL_W, weight=0)
            row_frame.grid_columnconfigure(tuple(range(1, len(langs) + 1)), weight=1)
            row_frame.grid_columnconfigure(len(langs) + 1, minsize=_ACT_COL_W, weight=0)

            # Key label
            key_cell = ctk.CTkFrame(row_frame, fg_color="transparent")
            key_cell.grid(row=0, column=0, padx=(12, 4), sticky="nsew")

            ctk.CTkLabel(
                key_cell,
                text=string.short_key,
                anchor="w",
                font=ctk.CTkFont(size=12, family="Courier"),
                text_color=("gray20", "gray80"),
                wraplength=_KEY_COL_W - 24,
            ).pack(side="left", fill="both", expand=True)

            if issues:
                ctk.CTkLabel(
                    key_cell, text="⚠",
                    text_color=("#E07B00", "#FFA040"),
                    font=ctk.CTkFont(size=11),
                ).pack(side="left", padx=(0, 4))

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

            # Delete button
            del_btn = ctk.CTkButton(
                row_frame,
                text="×",
                width=28,
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=16),
                fg_color="transparent",
                text_color=("gray50", "gray55"),
                hover_color=("#FFE0E0", "#5C1A1A"),
                command=lambda s=string: self._confirm_delete(s),
            )
            del_btn.grid(row=0, column=len(langs) + 1, padx=(4, 6), pady=5)

    def _build_add_row(self, langs: list[str]) -> None:
        """Inline row for adding a new key directly in the table."""
        add_frame = ctk.CTkFrame(
            self._rows_frame,
            fg_color=("gray88", "gray15"),
            corner_radius=5,
            height=_ROW_H + 4,
            border_width=1,
            border_color=("gray75", "gray30"),
        )
        add_frame.pack(fill="x", pady=(4, 2))
        add_frame.grid_propagate(False)
        add_frame.grid_columnconfigure(0, minsize=_KEY_COL_W, weight=0)
        add_frame.grid_columnconfigure(tuple(range(1, len(langs) + 1)), weight=1)
        add_frame.grid_columnconfigure(len(langs) + 1, minsize=_ACT_COL_W, weight=0)

        key_var = ctk.StringVar()
        error_var = ctk.StringVar()

        key_entry = ctk.CTkEntry(
            add_frame,
            textvariable=key_var,
            placeholder_text="new-key",
            font=ctk.CTkFont(size=12, family="Courier"),
            height=_ROW_H - 4,
            corner_radius=4,
            border_width=1,
        )
        key_entry.grid(row=0, column=0, padx=(8, 4), pady=4, sticky="ew")

        translation_vars: dict[str, ctk.StringVar] = {}
        translation_entries: list[ctk.CTkEntry] = []
        for col_i, lang in enumerate(langs):
            var = ctk.StringVar()
            translation_vars[lang] = var
            t_entry = ctk.CTkEntry(
                add_frame,
                textvariable=var,
                placeholder_text=lang,
                font=ctk.CTkFont(size=13),
                height=_ROW_H - 4,
                corner_radius=4,
                border_width=1,
            )
            t_entry.grid(row=0, column=col_i + 1, padx=(4, 4), pady=4, sticky="ew")
            translation_entries.append(t_entry)

        def _do_add() -> None:
            short = key_var.get().strip()
            if not short:
                key_entry.configure(border_color=("#E05555", "#C04040"))
                return
            full_key = f"{self._group}.{short}" if self._group else short
            translations = {l: v.get() for l, v in translation_vars.items()}
            if self._on_add_key:
                err = self._on_add_key(full_key, translations)
                if err:
                    # Widgets still alive — show error inline
                    key_entry.configure(border_color=("#E05555", "#C04040"))
                    error_var.set(err)
                    return
                # SUCCESS: _on_add_key triggered a full table rebuild.
                # All widgets in this closure are now destroyed — do not touch them.
                return
            # No callback: reset manually (widgets still alive)
            key_var.set("")
            for v in translation_vars.values():
                v.set("")
            key_entry.configure(border_color=("gray75", "gray32"))
            error_var.set("")

        # Reset border on typing
        key_var.trace_add("write", lambda *_: (
            key_entry.configure(border_color=("gray75", "gray32")),
            error_var.set(""),
        ))

        add_btn = ctk.CTkButton(
            add_frame,
            text="+",
            width=28,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=18),
            fg_color=("gray75", "gray30"),
            hover_color=("#3B82F6", "#2563EB"),
            text_color=("gray20", "gray90"),
            command=_do_add,
        )
        add_btn.grid(row=0, column=len(langs) + 1, padx=(4, 6), pady=5)
        key_entry.bind("<Return>", lambda _: _do_add())
        for t_entry in translation_entries:
            t_entry.bind("<Return>", lambda _: _do_add())

        # Error label row
        err_label = ctk.CTkLabel(
            self._rows_frame,
            textvariable=error_var,
            text_color=("#E05555", "#FF6B6B"),
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        err_label.pack(fill="x", padx=12)

    def _confirm_delete(self, string: LocaleString) -> None:
        """Show a modal confirmation before deleting a key from all locales."""
        if not self._on_delete_key:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Delete key")
        dlg.resizable(False, False)
        dlg.grab_set()

        # Centre over parent
        self.update_idletasks()
        px, py = self.winfo_rootx(), self.winfo_rooty()
        pw, ph = self.winfo_width(), self.winfo_height()
        dlg.geometry(f"380x160+{px + pw // 2 - 190}+{py + ph // 2 - 80}")

        ctk.CTkLabel(
            dlg,
            text=f'Delete  "{string.key}" ?',
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=340,
        ).pack(pady=(22, 6), padx=24)

        ctk.CTkLabel(
            dlg,
            text="This removes the key from every language file.",
            text_color=("gray50", "gray55"),
            font=ctk.CTkFont(size=12),
        ).pack()

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=18)

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=110,
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray40"),
            command=dlg.destroy,
        ).pack(side="left", padx=6)

        def _delete() -> None:
            dlg.destroy()
            self._on_delete_key(string)

        ctk.CTkButton(
            btn_row,
            text="Delete",
            width=110,
            fg_color=("#E05555", "#C04040"),
            hover_color=("#C04040", "#A03030"),
            command=_delete,
        ).pack(side="left", padx=6)
