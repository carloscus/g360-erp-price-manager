"""Warehouse badges: compact inventory display for per-warehouse stock counts."""

import flet as ft
from src.ui.theme import rgba, safe_page


class WarehouseBadges:
    def __init__(self, colors: dict, on_toggle_almacen=None):
        self.colors = colors
        self.on_toggle_almacen = on_toggle_almacen
        self._almacenes: dict[str, int] = {}
        self._visible: set[str] = set()
        self._badge_controls: dict[str, ft.Container] = {}

        self.container = ft.Row([], spacing=6, vertical_alignment="center")

    def get_control(self):
        return self.container

    def set_almacenes(self, almacenes: dict[str, int], visible: set[str] | None = None):
        self._almacenes = almacenes
        if visible is not None:
            self._visible = visible
        self._badge_controls.clear()
        self.container.controls.clear()

        for name, count in sorted(almacenes.items(), key=lambda x: (-x[1], x[0])):
            is_active = name in self._visible
            badge = self._make_badge(name, count, is_active)
            self._badge_controls[name] = badge
            self.container.controls.append(badge)

        if safe_page(self.container):
            self.container.update()

    def _make_badge(self, name: str, count: int, is_active: bool) -> ft.Container:
        bg = rgba(self.colors["accent"], 0.15) if is_active else rgba(ft.Colors.WHITE, 0.05)
        fg = self.colors["accent"] if is_active else self.colors["text_muted"]
        side = ft.BorderSide(1, self.colors["accent"]) if is_active else ft.BorderSide(1, "transparent")
        border = ft.Border(top=side, bottom=side, left=side, right=side)

        return ft.Container(
            content=ft.Row([
                ft.Text(f"Alm.{name}", size=9, color=fg, weight=ft.FontWeight.W_600),
                ft.Text(str(count), size=9, color=fg, weight=ft.FontWeight.W_800),
            ], spacing=3, tight=True),
            bgcolor=bg,
            border=border,
            border_radius=6,
            padding=ft.Padding(6, 3, 6, 3),
            on_click=lambda e, n=name: self._on_badge_click(n),
            ink=True,
        )

    def _on_badge_click(self, name: str):
        if name in self._visible:
            self._visible.discard(name)
        else:
            self._visible.add(name)
        self.set_almacenes(self._almacenes, self._visible)
        if self.on_toggle_almacen:
            self.on_toggle_almacen(name, name in self._visible)

    def get_visible_almacenes(self) -> set[str]:
        return self._visible
