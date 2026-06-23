import flet as ft
from src.ui.views.base_view import BaseView
from src.ui.theme import rgba
from src.ui.components.product_table import CONFIGURACION_COLUMNS


class ConfiguracionView(BaseView):
    def __init__(self, colors: dict, state=None, on_cell_edit=None,
                 on_category_assigned=None, on_units_per_box_change=None):
        super().__init__(colors)
        self.state = state
        self.on_cell_edit = on_cell_edit
        self.on_category_assigned = on_category_assigned
        self.on_units_per_box_change = on_units_per_box_change
        self._page_size = 75
        self._page = 0
        self._sort_column = "sequence"
        self._sort_desc = False
        self._filtered = []
        self._built = False
        self._filtro_categoria = ""
        self._filtro_sin_cat = ""  # "stock" | "nostock" | ""
        self._show_ean13 = False

    def build(self) -> ft.Control:
        if not self._built:
            self._build_controls()
        self._compute_data()
        self._sync_controls()
        self._sync_table()
        self._built = True
        return self._root

    def _compute_data(self):
        productos = self.state.productos if self.state else []

        # 1. FilterBar Filters (Search, Line, Type)
        filters = self.filter_bar.get_filters()
        busqueda = filters.get("busqueda", "").strip().lower()
        linea = filters.get("linea", "")
        tipo = filters.get("tipo", "")

        productos_filtrados = productos
        if busqueda:
            productos_filtrados = [p for p in productos_filtrados if busqueda in p.sku.lower() or busqueda in p.description.lower()]
        if linea:
            productos_filtrados = [p for p in productos_filtrados if p.line == linea]
        if tipo:
            productos_filtrados = [p for p in productos_filtrados if p.price_type == tipo]

        # 2. View-specific Category Filters
        if self._filtro_sin_cat == "stock":
            productos_filtrados = [p for p in productos_filtrados if not p.category and p.stock > 0]
        elif self._filtro_sin_cat == "nostock":
            productos_filtrados = [p for p in productos_filtrados if not p.category and p.stock <= 0]
        elif self._filtro_categoria:
            productos_filtrados = [p for p in productos_filtrados if p.category == self._filtro_categoria]
        else:
            # Default: show categorized products
            productos_filtrados = [p for p in productos_filtrados if p.category]

        self._filtered = productos_filtrados

        # 3. Determine max additional discounts across all products + pricing_rules
        max_adic = 3
        for p in productos:
            if p.additional_discounts:
                max_adic = max(max_adic, len(p.additional_discounts))
        pricing_rules = getattr(self.state, 'pricing_rules', None)
        if pricing_rules and hasattr(pricing_rules, 'additional_discounts'):
            for v in pricing_rules.additional_discounts.values():
                if isinstance(v, list):
                    max_adic = max(max_adic, len(v))

        # Build column list: base + conditional columns + Adic + price
        traductor = self.state.traductor if self.state else {}
        has_ean = any(p.ean13 and p.ean13.strip("0") for p in productos)
        cols = []
        for c in CONFIGURACION_COLUMNS:
            if c["key"] == "_sku_cliente" and not traductor:
                continue
            if c["key"] == "net_price":
                for i in range(1, max_adic + 1):
                    k = f"_adic{i:02d}"
                    cols.append({"key": k, "label": f"Adic{i}", "width": 50, "fmt": "adic", "align": "center"})
            cols.append(c)
        if has_ean and self._show_ean13:
            insert_at = next((i for i, c in enumerate(cols) if c["key"] == "units_per_box"), 2)
            cols.insert(insert_at + 1, {"key": "ean13", "label": "EAN13", "width": 95, "align": "left"})

        if not hasattr(self, '_table') or not self._table:
            from src.ui.components.product_table import ProductTable
            self._table = ProductTable(
                self.colors,
                columns=cols,
                on_cell_edit=self._on_cell_edit_wrapper,
                on_sort=self._on_sort,
            )
        else:
            self._table._columns = cols
        self._current_cols = cols
        if traductor:
            self._table.set_traductor(traductor)
        self._table.set_productos(self._filtered)

    def _build_controls(self):
        from src.ui.components.filter_bar import FilterBar
        from src.ui.components.pagination_bar import PaginationBar
        from src.ui.components.warehouse_badges import WarehouseBadges

        self.pagination = PaginationBar(
            self.colors,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_pag_size_change,
        )
        self.filter_bar = FilterBar(
            self.colors, 
            on_filter_change=self._on_filter,
            on_toggle_column=self._on_toggle_column
        )
        self.warehouse_badges = WarehouseBadges(
            self.colors, on_toggle_almacen=self._on_toggle_almacen,
        )
        self._table_ctl = ft.DataTable(
            columns=[], column_spacing=6,
            heading_row_height=32, data_row_min_height=32, data_row_max_height=44,
            horizontal_lines=ft.border.BorderSide(0.5, "white10"),
        )
        self._table_wrap = ft.Container(
            content=ft.Column([self._table_ctl], scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
            border=ft.Border.all(1, self.colors["border"]), border_radius=8, padding=4,
        )
        self._c_empty = ft.Container(
            content=ft.Column([
                ft.Text("Configuración", size=18, weight=ft.FontWeight.W_800, color=self.colors["text_primary"]),
                ft.Container(height=16),
                ft.Text("Carga archivos desde Actualizar Datos para ver la configuración",
                        size=12, color=self.colors["text_muted"], text_align="center"),
            ], horizontal_alignment="center", alignment=ft.Alignment.CENTER, spacing=0),
            expand=True, alignment=ft.Alignment.CENTER,
        )

        self._cat_dd = ft.Dropdown(
            hint_text="Categoría",
            width=140, height=36, text_size=11,
            bgcolor=rgba(ft.Colors.WHITE, 0.05),
            border_color=self.colors["border"],
            focused_border_color=self.colors["accent"],
            color="white",
            options=[ft.dropdown.Option("", "Todas")],
            on_select=self._on_categoria_change,
        )
        self._chip_stock = ft.Container(
            content=ft.Text("Stock sin cat.", size=10, color=self.colors["text_muted"]),
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=12,
            border=ft.Border.all(1, "white24"),
            on_click=self._on_chip_stock,
            ink=True,
        )
        self._chip_nostock = ft.Container(
            content=ft.Text("Sin stock sin cat.", size=10, color=self.colors["text_muted"]),
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=12,
            border=ft.Border.all(1, "white24"),
            on_click=self._on_chip_nostock,
            ink=True,
        )
        self._chip_ean13 = ft.Container(
            content=ft.Text("EAN13", size=10, color=self.colors["text_muted"]),
            padding=ft.Padding(8, 4, 8, 4),
            border_radius=12,
            border=ft.Border.all(1, "white24"),
            on_click=self._on_toggle_ean13,
            ink=True,
            visible=False,
        )

        header1 = ft.Row([
            ft.Text("Configuración Comercial", size=18, weight=ft.FontWeight.W_800, color=self.colors["text_primary"]),
            ft.Container(expand=True),
            self.warehouse_badges.get_control(),
        ], spacing=8, vertical_alignment="center")
        filter_row = ft.Container(
            content=self.filter_bar.get_control(),
            padding=ft.Padding(0, 0, 0, 0),
        )
        header2 = ft.Row([
            ft.Text("Categoría:", size=11, color=self.colors["text_muted"]),
            self._cat_dd,
            ft.Container(expand=True),
            self._chip_stock,
            self._chip_nostock,
        ], spacing=6, vertical_alignment="center")
        self._root = ft.Column([
            header1,
            filter_row,
            header2,
            self._c_empty,
            self._table_wrap,
            self.pagination.get_control(),
        ], spacing=8, expand=True)

    def _sync_controls(self):
        has_data = bool(self._filtered)
        self._c_empty.visible = not has_data
        self._table_wrap.visible = has_data
        self.pagination.get_control().visible = has_data
        lineas = self.state.lineas if self.state else []
        if lineas:
            self.filter_bar.set_lineas(lineas)
        todos = self.state.productos if self.state else []
        cats = sorted(set(p.category for p in todos if p.category))
        self._cat_dd.options = [ft.dropdown.Option("", "Todas")] + [
            ft.dropdown.Option(c, c) for c in cats
        ]
        has_ean = any(p.ean13 and p.ean13.strip("0") for p in (self.state.productos if self.state else []))
        self._chip_ean13.visible = has_ean
        ean_active = self._show_ean13
        self._chip_ean13.bgcolor = rgba(self.colors["accent"], 0.15) if ean_active else "transparent"
        self._chip_ean13.border = ft.Border.all(1, self.colors["accent"]) if ean_active else ft.Border.all(1, "white24")
        self._chip_ean13.content.color = self.colors["accent"] if ean_active else self.colors["text_muted"]

        almacenes_count: dict[str, int] = {}
        for p in self._filtered:
            sa = getattr(p, "warehouse_stock", {})
            if isinstance(sa, dict):
                for alm, val in sa.items():
                    qty = val[0] if isinstance(val, (list, tuple)) and len(val) > 0 else (val if isinstance(val, (int, float)) else 0)
                    if qty > 0:
                        almacenes_count[alm] = almacenes_count.get(alm, 0) + 1
        if almacenes_count:
            self.warehouse_badges.set_almacenes(almacenes_count)

    def _sync_table(self):
        if not hasattr(self, '_table_wrap') or not self._table_wrap:
            return
        if not hasattr(self, '_table') or not self._table:
            return
        self._table_ctl.columns = self._table.build_headers()
        self._table_ctl.rows = self._table.build_rows(self._page, self._page_size)
        try:
            self._table_ctl.update()
        except RuntimeError:
            pass
        if hasattr(self, 'pagination') and self.pagination:
            self.pagination.set_total(len(self._filtered), self._page, self._page_size)

    def _on_pag_size_change(self, size: int):
        self._page_size = size
        self._page = 0
        if self.state:
            self.state.pagina = 0
        self._sync_table()

    def _on_filter(self, filters: dict):
        self._page = 0
        if self.state:
            self.state.pagina = 0
        self._apply_filters()

    def _on_categoria_change(self, e):
        self._filtro_categoria = self._cat_dd.value or ""
        self._filtro_sin_cat = ""
        self._update_chips()
        self._page = 0
        if self.state:
            self.state.pagina = 0
        self._apply_filters()

    def _on_chip_stock(self, e):
        if self._filtro_sin_cat == "stock":
            self._filtro_sin_cat = ""
        else:
            self._filtro_sin_cat = "stock"
            self._filtro_categoria = ""
            self._cat_dd.value = ""
        self._update_chips()
        self._page = 0
        if self.state:
            self.state.pagina = 0
        self._apply_filters()

    def _on_chip_nostock(self, e):
        if self._filtro_sin_cat == "nostock":
            self._filtro_sin_cat = ""
        else:
            self._filtro_sin_cat = "nostock"
            self._filtro_categoria = ""
            self._cat_dd.value = ""
        self._update_chips()
        self._page = 0
        if self.state:
            self.state.pagina = 0
        self._apply_filters()

    def _update_chips(self):
        active_bg = rgba(self.colors["accent"], 0.15)
        active_border = ft.Border.all(1, self.colors["accent"])
        active_color = self.colors["accent"]
        default_bg = "transparent"
        default_border = ft.Border.all(1, "white24")
        default_color = self.colors["text_muted"]
        is_stock = self._filtro_sin_cat == "stock"
        is_nostock = self._filtro_sin_cat == "nostock"
        self._chip_stock.bgcolor = active_bg if is_stock else default_bg
        self._chip_stock.border = active_border if is_stock else default_border
        self._chip_stock.content.color = active_color if is_stock else default_color
        self._chip_nostock.bgcolor = active_bg if is_nostock else default_bg
        self._chip_nostock.border = active_border if is_nostock else default_border
        self._chip_nostock.content.color = active_color if is_nostock else default_color
        ean_active = self._show_ean13
        self._chip_ean13.bgcolor = active_bg if ean_active else default_bg
        self._chip_ean13.border = active_border if ean_active else default_border
        self._chip_ean13.content.color = active_color if ean_active else default_color

    def _apply_filters(self):
        self._compute_data()
        self._sync_controls()
        self._sync_table()
        if self._built:
            try:
                self._root.update()
            except RuntimeError:
                pass

    def _on_toggle_ean13(self, e):
        self._show_ean13 = not self._show_ean13
        self._update_chips()
        self._compute_data()
        self._sync_table()

    def _on_toggle_column(self, key: str, visible: bool):
        if key == "ean":
            self._show_ean13 = visible
            self._apply_filters()
        elif key == "sku_cliente":
            self._apply_filters()

    def _on_toggle_almacen(self, name: str, visible: bool):
        if hasattr(self, '_table'):
            self._table.set_extra_almacen(name, visible)
        self._sync_table()

    def _on_page_change(self, page: int):
        self._page = page
        if self.state:
            self.state.pagina = page

    def _on_sort(self, key: str, desc: bool):
        self._sort_column = key
        self._sort_desc = desc
        self._page = 0
        if self.state:
            self.state.pagina = 0
        productos = self._filtered
        if not productos:
            return
        key_fn = self._sort_key_fn(key)
        if key_fn:
            productos.sort(key=key_fn, reverse=desc)
        self._table.set_productos(productos)
        self._sync_table()

    @staticmethod
    def _sort_key_fn(key: str):
        if key == "sequence":
            return lambda p: getattr(p, "sequence", 0) or 0
        if key == "sku":
            return lambda p: p.sku or ""
        if key == "description":
            return lambda p: p.description or ""
        if key == "line":
            return lambda p: p.line or ""
        if key == "category":
            return lambda p: p.category or ""
        if key in ("units_per_box", "list_price", "net_price"):
            return lambda p: float(getattr(p, key, 0) or 0)
        if key == "_fixed_price":
            return lambda p: float(p.fixed_price or 0) if p.is_fixed_price() else -1.0
        if key.startswith("_adic"):
            idx = int(key.replace("_adic0", "").replace("_adic", "")) - 1
            def sort_key(p):
                adic = p.additional_discounts or []
                return float(adic[idx]) if idx < len(adic) else 0.0
            return sort_key
        if key == "_sku_cliente":
            return lambda p: p.customer_sku or ""
        if key.startswith("alm_"):
            alm = key[4:]
            def sort_key(p):
                raw = (p.warehouse_stock or {}).get(alm, 0)
                if isinstance(raw, (list, tuple)):
                    return raw[0] if len(raw) > 0 else 0
                return raw if isinstance(raw, (int, float)) else 0
            return sort_key
        return None

    def _on_cell_edit_wrapper(self, sku: str, col_key: str, value: str):
        if self.on_cell_edit:
            self.on_cell_edit(sku, col_key, value)
