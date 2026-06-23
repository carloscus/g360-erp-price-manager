"""Pagination bar: page navigation controls with configurable page size."""

import flet as ft
from src.ui.theme import rgba, safe_page, F_SMALL


class PaginationBar:
    def __init__(self, colors: dict, on_page_change=None, on_page_size_change=None):
        self.colors = colors
        self.on_page_change = on_page_change
        self.on_page_size_change = on_page_size_change
        self._total = 0
        self._page = 0
        self._page_size = 50
        self._total_pages = 0

        self._info = ft.Text("0-0 de 0", size=11, color=self.colors["text_muted"], weight=ft.FontWeight.W_500)

        self._go_input = ft.TextField(
            value="", width=45, height=28,
            text_size=11, text_align="center",
            dense=True, border_color=colors["border"],
            bgcolor=rgba(ft.Colors.WHITE, 0.04),
            color="white",
            content_padding=ft.Padding(2, 0, 2, 0),
            hint_text="P\u00e1g",
            on_submit=self._on_go_submit,
        )

        self._prev_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT_ROUNDED, icon_size=20,
            icon_color=colors["text_muted"],
            disabled=True,
            on_click=lambda e: self._go(self._page - 1),
            tooltip="P\u00e1gina anterior"
        )

        self._next_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_size=20,
            icon_color=colors["text_muted"],
            disabled=True,
            on_click=lambda e: self._go(self._page + 1),
            tooltip="Siguiente p\u00e1gina"
        )

        self._page_buttons = ft.Row(spacing=4)

        self._size_dropdown = ft.Dropdown(
            width=75, height=32, text_size=11,
            bgcolor=rgba(ft.Colors.WHITE, 0.05),
            border_color=colors["border"],
            color="white",
            options=[
                ft.dropdown.Option("25", "25"),
                ft.dropdown.Option("50", "50"),
                ft.dropdown.Option("100", "100"),
            ],
            value="50",
        )
        self._size_dropdown.on_change = self._on_size_change

        self.container = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SEGMENT, size=14, color=self.colors["text_muted"]),
                    self._info,
                ], spacing=8),
                ft.Container(expand=True),
                ft.Row([
                    self._prev_btn,
                    self._page_buttons,
                    self._next_btn,
                ], spacing=4),
                ft.Container(expand=True),
                ft.Row([
                    ft.Text("Ir a:", size=11, color=self.colors["text_muted"]),
                    self._go_input,
                    ft.VerticalDivider(width=1, color="white10"),
                    ft.Text("Filas:", size=11, color=self.colors["text_muted"]),
                    self._size_dropdown,
                ], spacing=8),
            ], spacing=0, vertical_alignment="center"),
            padding=ft.Padding(16, 8, 16, 8),
            bgcolor=rgba(self.colors["surface_light"], 0.4),
            border_radius=12,
            border=ft.Border.all(1, "white10"),
        )

    def get_control(self):
        return self.container

    def set_total(self, total: int, page: int = 0, page_size: int = 50):
        self._total = total
        self._page = page
        self._page_size = page_size
        self._total_pages = max(1, (total + page_size - 1) // page_size)
        self._update_display()

    def _update_display(self):
        start = self._page * self._page_size + 1 if self._total > 0 else 0
        end = min((self._page + 1) * self._page_size, self._total)
        self._info.value = f"{start}-{end} de {self._total} productos"
        self._prev_btn.disabled = self._page <= 0
        self._next_btn.disabled = self._page >= self._total_pages - 1

        self._page_buttons.controls.clear()
        for p in self._get_visible_pages():
            if p == -1:
                self._page_buttons.controls.append(
                    ft.Text("...", size=11, color=self.colors["text_muted"]))
            else:
                is_current = p == self._page
                self._page_buttons.controls.append(
                    ft.Container(
                        content=ft.Text(
                            str(p + 1),
                            size=11,
                            weight=ft.FontWeight.W_700 if is_current else ft.FontWeight.W_500,
                            color="white" if is_current else self.colors["text_muted"],
                        ),
                        width=32, height=32,
                        border_radius=8,
                        bgcolor=self.colors["accent"] if is_current else "transparent",
                        border=ft.Border.all(1, rgba(self.colors["accent"], 0.5)) if is_current else ft.Border.all(1, "white10"),
                        on_click=lambda e, pp=p: self._go(pp),
                        ink=True,
                        alignment=ft.Alignment(0, 0),
                        animate=ft.Animation(200, "easeOut"),
                    ))

        self._size_dropdown.value = str(self._page_size)

        if safe_page(self.container):
            self.container.update()

    def _get_visible_pages(self) -> list[int]:
        total = self._total_pages
        cur = self._page
        if total <= 7:
            return list(range(total))

        pages = [0]
        if cur > 3:
            pages.append(-1)

        start = max(1, cur - 1)
        end = min(total - 2, cur + 1)
        
        if cur < 3:
            end = 4
        if cur > total - 4:
            start = total - 5

        for i in range(start, end + 1):
            if i not in pages:
                pages.append(i)

        if cur < total - 4:
            if -1 not in pages[pages.index(end):]:
                pages.append(-1)

        if total - 1 not in pages:
            pages.append(total - 1)
        
        # Cleanup extra ellipsis
        final_pages = []
        for i, p in enumerate(pages):
            if p == -1 and i > 0 and pages[i-1] == -1:
                continue
            final_pages.append(p)
        return final_pages

    def _go(self, page: int):
        if 0 <= page < self._total_pages:
            self._page = page
            if self.on_page_change:
                self.on_page_change(page)

    def _on_go_submit(self, e=None):
        try:
            n = int(self._go_input.value or 0)
            if 1 <= n <= self._total_pages:
                self._go(n - 1)
            self._go_input.value = ""
        except (ValueError, TypeError):
            pass

    def _on_size_change(self, e):
        size = int(e.control.value or "50")
        self._page_size = size
        if self.on_page_size_change:
            self.on_page_size_change(size)
