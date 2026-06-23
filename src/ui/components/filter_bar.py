"""Filter bar: multi-line dropdown filter for product lines with active chips."""

import flet as ft
from src.ui.theme import rgba, safe_page


class FilterChip(ft.Container):
    def __init__(self, label: str, value: str, on_delete=None, colors=None):
        self.value = value
        self.colors = colors or {}
        super().__init__(
            content=ft.Row([
                ft.Text(label, size=10, weight=ft.FontWeight.W_600, color="white"),
                ft.Icon(ft.Icons.CLOSE, size=12, color="white70"),
            ], spacing=4, tight=True),
            bgcolor=rgba(self.colors["accent"], 0.25),
            border=ft.Border.all(1, rgba(self.colors["accent"], 0.5)),
            border_radius=15,
            padding=ft.Padding(10, 4, 8, 4),
            on_click=lambda _: on_delete(value) if on_delete else None,
            animate=ft.Animation(200, "easeOut"),
        )


class FilterBar:
    def __init__(self, colors: dict, on_filter_change=None, on_toggle_column=None):
        self.colors = colors
        self.on_filter_change = on_filter_change
        self.on_toggle_column = on_toggle_column
        self._active_columns = {
            "ean": False,
            "sku_cliente": False,
        }

        self.search_field = ft.TextField(
            hint_text="Buscar SKU o nombre...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=25,
            height=36,
            width=220,
            text_size=11,
            bgcolor=rgba(ft.Colors.WHITE, 0.05),
            border_color=colors["border"],
            focused_border_color=colors["accent"],
            color="white",
            on_change=self._on_change,
            on_submit=self._on_change,
        )

        self.linea_dropdown = ft.Dropdown(
            hint_text="Línea",
            width=160,
            height=40,
            text_size=11,
            bgcolor=rgba(ft.Colors.WHITE, 0.08),
            border_color="white24",
            focused_border_color=colors["accent"],
            color="white",
            options=[ft.dropdown.Option("", "Todas")],
        )
        self.linea_dropdown.content_padding = ft.Padding(10, 0, 10, 0)
        self.linea_dropdown.alignment = ft.Alignment(-1, 0)
        self.linea_dropdown.on_change = self._on_dropdown_change

        self.tipo_dropdown = ft.Dropdown(
            hint_text="Tipo",
            width=120,
            height=40,
            text_size=11,
            bgcolor=rgba(ft.Colors.WHITE, 0.08),
            border_color="white24",
            focused_border_color=colors["accent"],
            color="white",
            options=[
                ft.dropdown.Option("", "Todos"),
                ft.dropdown.Option("NORMAL", "Normal"),
                ft.dropdown.Option("FIJO", "Fijo"),
            ],
        )
        self.tipo_dropdown.content_padding = ft.Padding(10, 0, 10, 0)
        self.tipo_dropdown.alignment = ft.Alignment(-1, 0)
        self.tipo_dropdown.on_change = self._on_dropdown_change

        self.chips_row = ft.Row(spacing=6, wrap=True)
        
        # Column toggles (EAN, SKU Cliente)
        self.ean_chip = self._make_toggle_chip("EAN (13/14)", "ean", ft.Icons.BARCODE_READER)
        self.sku_cliente_chip = self._make_toggle_chip("SKU Cliente", "sku_cliente", ft.Icons.PERSON_PIN_ROUNDED)

        self.container = ft.Column([
            ft.Row([
                self.search_field,
                self.linea_dropdown,
                self.tipo_dropdown,
                ft.VerticalDivider(width=1, color="white10"),
                ft.Row([
                    ft.Text("Columnas:", size=10, color=self.colors["text_muted"], weight=ft.FontWeight.W_600),
                    self.ean_chip,
                    self.sku_cliente_chip,
                ], spacing=6),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_size=18,
                    icon_color=self.colors["text_muted"],
                    tooltip="Limpiar filtros",
                    on_click=lambda _: self.reset()
                )
            ], spacing=8, vertical_alignment="center"),
            self.chips_row
        ], spacing=8)

    def _make_toggle_chip(self, label: str, key: str, icon: str) -> ft.Container:
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=14, color=self.colors["text_muted"]),
                ft.Text(label, size=10, color=self.colors["text_muted"]),
            ], spacing=4, tight=True),
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=15,
            border=ft.Border.all(1, "white10"),
            bgcolor="transparent",
            on_click=lambda _: self._toggle_column(key),
            ink=True,
            animate=ft.Animation(200, "easeOut"),
        )

    def _toggle_column(self, key: str):
        self._active_columns[key] = not self._active_columns[key]
        is_active = self._active_columns[key]
        chip = self.ean_chip if key == "ean" else self.sku_cliente_chip
        
        chip.bgcolor = rgba(self.colors["accent"], 0.15) if is_active else "transparent"
        chip.border = ft.Border.all(1, self.colors["accent"]) if is_active else ft.Border.all(1, "white10")
        chip.content.controls[0].color = self.colors["accent"] if is_active else self.colors["text_muted"]
        chip.content.controls[1].color = self.colors["accent"] if is_active else self.colors["text_muted"]
        
        if safe_page(chip):
            chip.update()
        
        if self.on_toggle_column:
            self.on_toggle_column(key, is_active)

    def get_control(self):
        return self.container

    def set_lineas(self, lineas: list[str]):
        self.linea_dropdown.options = [ft.dropdown.Option("", "Todas")] + [
            ft.dropdown.Option(l, l) for l in sorted(lineas)
        ]
        if safe_page(self.linea_dropdown):
            self.linea_dropdown.update()

    def get_filters(self) -> dict:
        return {
            "busqueda": self.search_field.value or "",
            "linea": self.linea_dropdown.value or "",
            "tipo": self.tipo_dropdown.value or "",
        }

    def _on_dropdown_change(self, e):
        self._update_chips()
        self._on_change(e)

    def _update_chips(self):
        self.chips_row.controls.clear()
        filters = self.get_filters()

        if filters["linea"]:
            self.chips_row.controls.append(
                FilterChip(f"Línea: {filters['linea']}", "linea", self._remove_filter, colors=self.colors)
            )
        if filters["tipo"]:
            self.chips_row.controls.append(
                FilterChip(f"Tipo: {filters['tipo']}", "tipo", self._remove_filter, colors=self.colors)
            )

        if safe_page(self.chips_row):
            self.chips_row.update()

    def _remove_filter(self, key: str):
        if key == "linea":
            self.linea_dropdown.value = ""
        elif key == "tipo":
            self.tipo_dropdown.value = ""
        self._update_chips()
        self._on_change()

    def _on_change(self, e=None):
        if self.on_filter_change:
            self.on_filter_change(self.get_filters())

    def reset(self):
        self.search_field.value = ""
        self.linea_dropdown.value = ""
        self.tipo_dropdown.value = ""
        self._active_columns = {k: False for k in self._active_columns}
        
        # Reset chips visual state
        for chip in [self.ean_chip, self.sku_cliente_chip]:
            chip.bgcolor = "transparent"
            chip.border = ft.Border.all(1, "white10")
            chip.content.controls[0].color = self.colors["text_muted"]
            chip.content.controls[1].color = self.colors["text_muted"]
            if safe_page(chip):
                chip.update()

        self._update_chips()
        self._on_change()
