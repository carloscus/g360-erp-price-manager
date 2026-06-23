"""Status panel: loading spinner and status message bar at the bottom of the main view."""

import flet as ft
from src.ui.theme import rgba, safe_page


class StatusPanel:
    def __init__(self, colors: dict):
        self.colors = colors
        self._status_text = ft.Text("", size=11, color=colors["text_muted"], weight=ft.FontWeight.W_500)
        self._progress = ft.ProgressBar(width=200, color=colors["accent"], visible=False, height=2)

        self.container = ft.Row([
            self._status_text,
            self._progress,
        ], spacing=10, vertical_alignment="center")

    def get_control(self):
        return self.container

    def set_status(self, message: str, level: str = "muted"):
        color_map = {
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "error": self.colors["error"],
            "muted": self.colors["text_muted"],
            "accent": self.colors["accent"],
        }
        self._status_text.value = message
        self._status_text.color = color_map.get(level, self.colors["text_muted"])
        if safe_page(self.container):
            self.container.update()

    def set_loading(self, loading: bool, message: str = ""):
        self._progress.visible = loading
        if message:
            self._status_text.value = message
        if safe_page(self.container):
            self.container.update()

    def refresh_colors(self, colors: dict):
        self.colors = colors
        self._status_text.color = colors["text_muted"]
        self._progress.color = colors["accent"]
