from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class AddKeyDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        group: str,
        languages: list[str],
        on_confirm: Callable[[str, dict[str, str]], None],
    ):
        super().__init__(master)
        self.title("Add Key")
        self.resizable(False, False)
        self._on_confirm = on_confirm

        self.grid_columnconfigure(0, weight=1)

        row = 0
        ctk.CTkLabel(
            self, text="Key path", anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=row, column=0, padx=20, pady=(20, 4), sticky="ew")
        row += 1

        prefix = f"{group}." if group else ""
        self._key_entry = ctk.CTkEntry(self, placeholder_text=f"{prefix}key_name")
        if group:
            self._key_entry.insert(0, prefix)
        self._key_entry.grid(row=row, column=0, padx=20, sticky="ew")
        row += 1

        self._lang_entries: dict[str, ctk.CTkEntry] = {}
        for lang in languages:
            ctk.CTkLabel(
                self, text=lang.upper(), anchor="w",
                font=ctk.CTkFont(weight="bold"),
            ).grid(row=row, column=0, padx=20, pady=(14, 4), sticky="ew")
            row += 1
            entry = ctk.CTkEntry(self, placeholder_text=f"Translation in {lang}…")
            entry.grid(row=row, column=0, padx=20, sticky="ew")
            self._lang_entries[lang] = entry
            row += 1

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=row, column=0, padx=20, pady=20, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Cancel", width=80,
            fg_color="transparent", border_width=1, command=self.destroy,
        ).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Add Key", command=self._confirm).pack(side="left")

        height = min(600, 170 + len(languages) * 76)
        self.geometry(f"440x{height}")
        self._key_entry.focus()
        self.bind("<Escape>", lambda _: self.destroy())

    def _confirm(self) -> None:
        key = self._key_entry.get().strip().strip(".")
        if not key:
            return
        translations = {lang: e.get() for lang, e in self._lang_entries.items()}
        self.destroy()
        self._on_confirm(key, translations)
