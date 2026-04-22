from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import customtkinter as ctk

from models.locale_string import LocaleString
from models.project import Project


# ── Tree helpers ───────────────────────────────────────────────────────────────

@dataclass
class SidebarNode:
    name: str
    full_path: str
    has_keys: bool
    children: list["SidebarNode"] = field(default_factory=list)


def _derive_group_tree(strings: list[LocaleString]) -> list[SidebarNode]:
    """Build a tree of SidebarNodes from the groups present in *strings*."""
    direct_groups: set[str] = set()
    for s in strings:
        if s.group:
            direct_groups.add(s.group)

    all_groups: set[str] = set()
    for g in direct_groups:
        parts = g.split(".")
        for i in range(1, len(parts) + 1):
            all_groups.add(".".join(parts[:i]))

    nodes: dict[str, SidebarNode] = {}
    for path in all_groups:
        name = path.rsplit(".", 1)[-1]
        nodes[path] = SidebarNode(name=name, full_path=path, has_keys=path in direct_groups)

    roots: list[SidebarNode] = []
    for path, node in nodes.items():
        parent = ".".join(path.split(".")[:-1])
        if parent and parent in nodes:
            nodes[parent].children.append(node)
        else:
            roots.append(node)

    def _sort(n: SidebarNode) -> None:
        n.children.sort(key=lambda c: c.name)
        for c in n.children:
            _sort(c)

    roots.sort(key=lambda n: n.name)
    for r in roots:
        _sort(r)

    return roots


# ── Sidebar widget ─────────────────────────────────────────────────────────────

class Sidebar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_group_selected: Callable[[Project, str], None],
        on_project_removed: Callable[[Project], None],
        on_add_locale: Callable[[Project], None],
        width: int = 260,
        **kwargs,
    ):
        super().__init__(
            master, width=width,
            fg_color=("gray87", "gray17"),
            corner_radius=8,
            **kwargs,
        )
        self.grid_propagate(False)

        self._on_group_selected = on_group_selected
        self._on_project_removed = on_project_removed
        self._on_add_locale = on_add_locale

        # State
        self._data: list[tuple[Project, list[SidebarNode]]] = []
        self._expanded: set[str] = set()
        self._selected: str | None = None  # "project_name::group_full_path"

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
        )
        self._scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._scroll.grid_columnconfigure(0, weight=1)

        self._render()

    # ── Public API ─────────────────────────────────────────────────────────

    def set_data(self, data: list[tuple[Project, list[LocaleString]]]) -> None:
        new_data = [
            (project, _derive_group_tree(strings))
            for project, strings in data
        ]
        # Auto-expand any project not previously known
        known = {p.name for p, _ in self._data}
        for project, _ in new_data:
            if project.name not in known:
                self._expanded.add(f"P:{project.name}")
        self._data = new_data
        self._render()

    def set_selected(self, project_name: str, group: str) -> None:
        self._selected = f"{project_name}::{group}"
        self._render()

    # ── Rendering ──────────────────────────────────────────────────────────

    def _render(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        if not self._data:
            ctk.CTkLabel(
                self._scroll,
                text="No projects yet.\n\nClick  + Project  in the toolbar\nto get started.",
                text_color=("gray55", "gray50"),
                justify="center",
                wraplength=210,
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, pady=50, padx=20)
            return

        row = 0
        for project, tree_nodes in self._data:
            row = self._render_project_row(project, tree_nodes, row)
            exp_key = f"P:{project.name}"
            if exp_key in self._expanded:
                if tree_nodes:
                    for node in tree_nodes:
                        row = self._render_node(node, project, indent=1, row=row)
                else:
                    # Project has locale files but no keys yet — show placeholder
                    row = self._render_empty_project(project, row)
            # Spacer between projects
            ctk.CTkFrame(
                self._scroll, height=4, fg_color="transparent",
            ).grid(row=row, column=0)
            row += 1

    def _render_project_row(self, project: Project, tree_nodes: list, row: int) -> int:
        exp_key = f"P:{project.name}"
        is_exp = exp_key in self._expanded
        arrow = "▾" if is_exp else "▸"
        is_selected = self._selected == f"{project.name}::"

        bg = ("gray76", "gray26") if is_selected else ("gray80", "gray22")

        frame = ctk.CTkFrame(
            self._scroll,
            fg_color=bg,
            height=36, corner_radius=7,
        )
        frame.grid(row=row, column=0, sticky="ew", padx=2, pady=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_propagate(False)

        ctk.CTkButton(
            frame, text=arrow, width=26, height=26,
            fg_color="transparent", hover_color=("gray72", "gray28"),
            text_color=("gray40", "gray60"), font=ctk.CTkFont(size=13),
            command=lambda k=exp_key: self._toggle(k),
        ).grid(row=0, column=0, padx=(4, 0), pady=4)

        # Clicking the project name selects it as current context (root group "")
        name_color = ("gray5", "white") if is_selected else ("gray10", "gray92")
        ctk.CTkButton(
            frame, text=project.name, anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent", hover_color=("gray72", "gray28"),
            text_color=name_color,
            command=lambda p=project, k=exp_key: self._select_project(p, k),
        ).grid(row=0, column=1, sticky="ew", padx=0, pady=4)

        # Language count badge
        lang_count = len(project.locale_files)
        if lang_count:
            ctk.CTkLabel(
                frame,
                text=str(lang_count),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=("gray50", "gray55"),
                fg_color=("gray72", "gray30"),
                corner_radius=8,
                width=20, height=16,
            ).grid(row=0, column=2, padx=4)

        ctk.CTkButton(
            frame, text="+", width=24, height=24,
            fg_color="transparent", hover_color=("gray72", "gray28"),
            text_color=("gray40", "gray60"), font=ctk.CTkFont(size=15),
            command=lambda p=project: self._on_add_locale(p),
        ).grid(row=0, column=3, padx=(0, 2), pady=4)

        ctk.CTkButton(
            frame, text="✕", width=24, height=24,
            fg_color="transparent", hover_color=("#FECACA", "#7F1D1D"),
            text_color=("gray55", "gray50"), font=ctk.CTkFont(size=11),
            command=lambda p=project: self._on_project_removed(p),
        ).grid(row=0, column=4, padx=(0, 4), pady=4)

        return row + 1

    def _render_empty_project(self, project: Project, row: int) -> int:
        """Render a placeholder row when a project has locale files but no keys."""
        is_selected = self._selected == f"{project.name}::"
        bg = ("gray78", "gray26") if is_selected else "transparent"
        frame = ctk.CTkFrame(self._scroll, fg_color=bg, height=30, corner_radius=5)
        frame.grid(row=row, column=0, sticky="ew", padx=2, pady=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_propagate(False)
        ctk.CTkButton(
            frame,
            text="No keys yet  —  click + Key to start",
            anchor="w",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray55"),
            fg_color="transparent",
            hover_color=("gray74", "gray30"),
            command=lambda p=project: self._select_project(p, f"P:{p.name}"),
        ).grid(row=0, column=0, sticky="ew", padx=(28, 0))
        return row + 1

    def _render_node(
        self, node: SidebarNode, project: Project, indent: int, row: int,
    ) -> int:
        sel_key = f"{project.name}::{node.full_path}"
        exp_key = f"G:{project.name}:{node.full_path}"
        is_selected = self._selected == sel_key
        is_exp = exp_key in self._expanded
        has_children = bool(node.children)

        bg = ("gray78", "gray26") if is_selected else "transparent"
        fg_text = ("gray5", "white") if is_selected else ("gray20", "gray85")

        frame = ctk.CTkFrame(
            self._scroll, fg_color=bg, height=30, corner_radius=5,
        )
        frame.grid(row=row, column=0, sticky="ew", padx=2, pady=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_propagate(False)

        indent_pad = indent * 16

        # Toggle / bullet
        if has_children:
            arrow = "▼" if is_exp else "▶"
            ctk.CTkButton(
                frame, text=arrow, width=20, height=20,
                fg_color="transparent", hover_color=("gray74", "gray30"),
                text_color=("gray40", "gray60"), font=ctk.CTkFont(size=10),
                command=lambda k=exp_key: self._toggle(k),
            ).grid(row=0, column=0, padx=(indent_pad, 0), pady=4)
        else:
            ctk.CTkLabel(
                frame, text="●", width=20,
                text_color=("gray55", "gray55"), font=ctk.CTkFont(size=8),
            ).grid(row=0, column=0, padx=(indent_pad, 0), pady=4)

        # Name label / button
        ctk.CTkButton(
            frame, text=node.name, anchor="w",
            font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color=("gray74", "gray30"),
            text_color=fg_text,
            command=lambda p=project, g=node.full_path: self._select_group(p, g),
        ).grid(row=0, column=1, sticky="ew", padx=0, pady=4)

        row += 1

        # Recursively render children if expanded
        if has_children and is_exp:
            for child in node.children:
                row = self._render_node(child, project, indent + 1, row)

        return row

    # ── Interaction ────────────────────────────────────────────────────────

    def _toggle(self, key: str) -> None:
        if key in self._expanded:
            self._expanded.discard(key)
        else:
            self._expanded.add(key)
        self._render()

    def _select_project(self, project: Project, exp_key: str) -> None:
        """Select the project at root level and ensure it is expanded."""
        self._selected = f"{project.name}::"
        self._expanded.add(exp_key)
        self._render()
        self._on_group_selected(project, "")

    def _select_group(self, project: Project, group: str) -> None:
        self._selected = f"{project.name}::{group}"
        self._render()
        self._on_group_selected(project, group)
