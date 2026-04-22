from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class AddGroupDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        parent_group: str,
        on_confirm: Callable[[str], None],
    ):
        super().__init__(master)
        self.title("Add Group")
        self.geometry("420x190")
        self.resizable(False, False)
        self._on_confirm = on_confirm

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Group path", anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="ew")

        self._entry = ctk.CTkEntry(
            self, placeholder_text=f"{parent_group + '.' if parent_group else ''}group_name"
        )
        if parent_group:
            self._entry.insert(0, parent_group + ".")
        self._entry.grid(row=1, column=0, padx=20, sticky="ew")
        self._entry.focus()

        ctk.CTkLabel(
            self, text="Groups are inferred from key prefixes (e.g. 'auth.login')",
            text_color=("gray55", "gray55"), font=ctk.CTkFont(size=12), anchor="w",
        ).grid(row=2, column=0, padx=20, pady=(6, 0), sticky="ew")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=20, pady=20, sticky="e")

        ctk.CTkButton(
            btn_frame, text="Cancel", width=80,
            fg_color="transparent", border_width=1, command=self.destroy,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_frame, text="Add Group", command=self._confirm,
        ).pack(side="left")

        self.bind("<Return>", lambda _: self._confirm())
        self.bind("<Escape>", lambda _: self.destroy())

    def _confirm(self) -> None:
        value = self._entry.get().strip().strip(".")
        if not value:
            return
        self.destroy()
        self._on_confirm(value)
