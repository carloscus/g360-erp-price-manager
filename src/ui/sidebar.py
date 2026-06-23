"""Sidebar navigation: 3 views + theme toggle."""

import flet as ft
from src.ui.theme import rgba, safe_page, F_SMALL, F_TINY

try:
    from g360_flet.g360_signature import G360Signature
except ImportError:
    G360Signature = None


class G360Sidebar:
    NUM_VIEWS = 3
    VIEW_NAMES = ["Lista Precios", "Configuración", "Actualizar Datos"]
    VIEW_ICONS = [
        (ft.Icons.PRICE_CHANGE_OUTLINED, ft.Icons.PRICE_CHANGE),
        (ft.Icons.TUNE_OUTLINED, ft.Icons.TUNE),
        (ft.Icons.CLOUD_SYNC_OUTLINED, ft.Icons.CLOUD_SYNC),
    ]
    STORAGE_KEY = "price_manager_view"

    def __init__(self, on_nav_change, colors: dict, on_theme_toggle=None):
        self.on_nav_change = on_nav_change
        self.on_theme_toggle = on_theme_toggle
        self.colors = colors
        self._is_extended = False
        self._last_view_index = 0
        self._dark = True

        self.menu_button = ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=colors["text_muted"],
            on_click=self._toggle_sidebar,
            tooltip="Expandir/Colapsar",
        )

        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            icon_color=colors["text_muted"],
            on_click=self._toggle_theme,
            tooltip="Cambiar tema",
        )

        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type="all",
            min_width=80,
            min_extended_width=220,
            extended=False,
            expand=True,
            bgcolor="transparent",
            indicator_color=rgba(colors["accent"], 0.12),
            indicator_shape=ft.RoundedRectangleBorder(radius=8),
            unselected_label_text_style=ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_500, color=colors["text_muted"]),
            selected_label_text_style=ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_600, color=colors["accent"]),
            leading=ft.Container(
                content=self.menu_button,
                padding=ft.Padding(top=10, bottom=0),
                alignment=ft.Alignment(0, 0),
            ),
            destinations=[],
            on_change=self._on_nav_change,
        )

        self._g360_footer = (
            G360Signature(mode="powered", version="2.0") if G360Signature
            else ft.Text("Powered by G360", color=colors["text_muted"], size=F_TINY, weight=ft.FontWeight.W_400)
        )

        self._color_indicator = ft.Container(
            width=3, height=0, bgcolor=colors["accent"],
            border_radius=ft.BorderRadius(top_right=2, bottom_right=2, top_left=0, bottom_left=0),
            animate=ft.Animation(300, "decelerate"),
        )

        self.divider = ft.Divider(height=1, color=colors["border"])
        self.container = ft.Container(
            content=ft.Stack([
                ft.Column([
                    self.nav_rail,
                    ft.Container(
                        content=ft.Column([
                            self.divider,
                            self.theme_button,
                            ft.Container(
                                content=self._g360_footer,
                                alignment=ft.Alignment(0, 0),
                                padding=ft.Padding(left=0, top=4, right=0, bottom=12),
                            ),
                        ], spacing=0, horizontal_alignment="center"),
                    ),
                ], expand=True, spacing=0),
                self._color_indicator,
            ]),
            width=80,
            bgcolor=colors["surface"],
            border=ft.Border(right=ft.BorderSide(1, colors["border"])),
            clip_behavior="hardEdge",
            animate=ft.Animation(400, "decelerate"),
        )

        self._rebuild_destinations()
        self._update_indicator(0)

    def _rebuild_destinations(self):
        labels = self.VIEW_NAMES[:]
        dests = []
        for i, (icons, label) in enumerate(zip(self.VIEW_ICONS, labels)):
            icon_out, icon_in = icons
            dests.append(
                ft.NavigationRailDestination(
                    icon=icon_out, selected_icon=icon_in, label=label,
                )
            )
        self.nav_rail.destinations = dests
        if safe_page(self.container):
            self.nav_rail.update()

    def _toggle_sidebar(self, e):
        self._is_extended = not self._is_extended
        self.nav_rail.extended = self._is_extended
        self.container.width = 220 if self._is_extended else 80
        self.menu_button.icon = ft.Icons.MENU_OPEN if self._is_extended else ft.Icons.MENU
        self._g360_footer.visible = self._is_extended
        self._rebuild_destinations()
        self.container.update()

    def _toggle_theme(self, e):
        self._dark = not self._dark
        self.theme_button.icon = ft.Icons.DARK_MODE if self._dark else ft.Icons.LIGHT_MODE
        self.theme_button.update()
        if self.on_theme_toggle:
            self.on_theme_toggle(self._dark)

    def _on_nav_change(self, e):
        idx = e.control.selected_index
        if self._last_view_index == idx:
            return
        self._last_view_index = idx
        if 0 <= idx < self.NUM_VIEWS:
            self._update_indicator(idx)
        self.on_nav_change(e)

    def _update_indicator(self, idx: int):
        vc = [self.colors["accent"], self.colors["warning"], self.colors["info"]]
        color = vc[idx] if 0 <= idx < self.NUM_VIEWS else self.colors["accent"]
        self._color_indicator.bgcolor = color
        self._color_indicator.height = 40
        self.nav_rail.selected_label_text_style = ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_600, color=color)
        self.nav_rail.indicator_color = rgba(color, 0.12)
        self._last_view_index = idx
        if safe_page(self.container):
            self.container.update()

    def set_loading(self, loading: bool):
        if loading:
            self.nav_rail.leading = ft.Container(
                content=ft.Column([
                    ft.ProgressRing(width=24, height=24, stroke_width=2, color=self.colors["accent"]),
                    ft.Text("Cargando...", size=F_SMALL, color=self.colors["text_muted"]),
                ], horizontal_alignment="center", spacing=4),
                padding=ft.Padding(top=10, bottom=10),
            )
        else:
            self.nav_rail.leading = ft.Container(
                content=self.menu_button,
                padding=ft.Padding(top=10, bottom=0),
                alignment=ft.Alignment(0, 0),
            )
            self.menu_button.icon = ft.Icons.MENU_OPEN if self._is_extended else ft.Icons.MENU
        self.nav_rail.update()

    def refresh_theme(self, colors: dict):
        self.colors = colors
        self.container.bgcolor = colors["surface"]
        self.container.border = ft.Border(right=ft.BorderSide(1, colors["border"]))
        self.divider.color = colors["border"]
        self.menu_button.icon_color = colors["text_muted"]
        self.theme_button.icon_color = colors["text_muted"]
        self.nav_rail.unselected_label_text_style = ft.TextStyle(
            size=F_SMALL, weight=ft.FontWeight.W_500, color=colors["text_muted"]
        )
        if safe_page(self.container):
            self.container.update()

    def restore_state(self, page: ft.Page):
        try:
            saved = page.client_storage.get(self.STORAGE_KEY)
            if saved is not None:
                idx = int(saved)
                if 0 <= idx < self.NUM_VIEWS:
                    self.nav_rail.selected_index = idx
                    self._update_indicator(idx)
        except Exception:
            pass

    def save_state(self, page: ft.Page, index: int):
        try:
            page.client_storage.set(self.STORAGE_KEY, index)
        except Exception:
            pass
