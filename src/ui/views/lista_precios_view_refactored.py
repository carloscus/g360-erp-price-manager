"""Vista de Lista de Precios: una categoria por vez, header limpio."""

import flet as ft
from src.ui.views.base_view import BaseView
from src.ui.theme import rgba
from src.ui.components.product_table import LISTA_PRECIOS_ALL, filtrar_columnas, ProductTable
from src.ui.components.control_categorias import ControlCategoriasOnDemand
from src.ui.components.pagination_bar import PaginationBar
from src.ui.components.warehouse_badges import WarehouseBadges
from src.core.lazy_data_manager import LazyDataManager
from src.core.models import DescuentosCategoria

# (key, label, numeric_input)
DISCOUNT_DEFS = [
    ("_desc01", "D1", True),
    ("_desc02", "D2", True),
    ("_desc03", "D3", True),
    ("_desc04", "D4", True),
    ("_rebate", "Reb.", True),
    ("_custom", "Esp.", False),
]


class ListaPreciosViewRefactored(BaseView):
    """Una categoria por vez. Header limpio: dropdown + busqueda + tabla."""

    def __init__(self, colors: dict, lazy_manager: LazyDataManager, state=None,
                 on_file_loaded=None, on_desc_quick_apply=None,
                 on_toggle_almacen=None, on_cell_edit=None,
                 on_selection_change=None, on_page_change=None,
                 on_lista_select=None, on_export_json=None,
                 on_export_xlsx=None, on_save_cliente_list=None,
                 on_export_xlsx_formulas=None):
        super().__init__(colors)
        self.lazy_manager = lazy_manager
        self.state = state
        self.on_file_loaded = on_file_loaded
        self.on_desc_quick_apply = on_desc_quick_apply
        self.on_toggle_almacen = on_toggle_almacen
        self.on_cell_edit = on_cell_edit
        self.on_selection_change = on_selection_change
        self.on_page_change = on_page_change
        self.on_lista_select = on_lista_select
        self.on_export_json = on_export_json
        self.on_export_xlsx = on_export_xlsx
        self.on_save_cliente_list = on_save_cliente_list
        self.on_export_xlsx_formulas = on_export_xlsx_formulas

        self._page_size = 50
        self._page = 0
        self._sort_column = "sequence"
        self._sort_desc = False
        self._filtered = []
        self._built = False
        self._busqueda = ""
        self._control_categorias: ControlCategoriasOnDemand | None = None
        self._table: ProductTable | None = None
        self._show_ean13 = False
        self._discount_toggles: dict[str, bool] = {k: False for k, _, _ in DISCOUNT_DEFS}
        self._discount_chips: dict[str, ft.Container] = {}
        self._discount_inputs: dict[str, ft.TextField] = {}

    def build(self) -> ft.Control:
        if not self._built:
            self._build_controls()
            self._built = True
        self.inicializar_categorias()
        self._compute_data()
        self._sync_controls()
        self._sync_table()
        return self._root

    def _build_controls(self):
        self.pagination = PaginationBar(
            self.colors,
            on_page_change=self._on_page_change,
            on_page_size_change=self._on_pag_size_change,
        )

        self._control_categorias = ControlCategoriasOnDemand(
            lazy_manager=self.lazy_manager, colors=self.colors,
            state=self.state,
            on_categoria_seleccionada=self._on_categoria_seleccionada,
            on_descuentos_cambiados=self._on_descuentos_cambiados,
        )

        self._search_field = ft.TextField(
            hint_text="Buscar SKU o nombre...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=25,
            height=34,
            width=240,
            text_size=11,
            dense=True,
            bgcolor=rgba(ft.Colors.WHITE, 0.04),
            border_color="white24",
            focused_border_color=self.colors["accent"],
            color=self.colors["text_primary"],
            on_change=self._on_search,
            on_submit=self._on_search,
        )

        self._table_ctl = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(""))], column_spacing=6,
            heading_row_height=32, data_row_min_height=32, data_row_max_height=44,
            horizontal_lines=ft.border.BorderSide(0.5, "white10"),
        )
        self._table_wrap = ft.Container(
            content=ft.Row([self._table_ctl], scroll=ft.ScrollMode.AUTO),
            border=ft.Border.all(1, self.colors["border"]),
            border_radius=8, padding=4,
            visible=False,
        )

        self._c_empty = ft.Container(
            content=ft.Column([
                ft.Text("Lista de Precios", size=18, weight=ft.FontWeight.W_800, color=self.colors["text_primary"]),
                ft.Container(height=12),
                ft.Text("Seleccione una categoria para editar", size=12, color=self.colors["text_muted"]),
            ], horizontal_alignment="center", alignment=ft.Alignment.CENTER, spacing=0),
            expand=True, alignment=ft.Alignment.CENTER,
        )

        self._scrollable_body = ft.Column([
            self._c_empty,
            self._table_wrap,
        ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)

        export_row = ft.Row([
            ft.OutlinedButton("XLSX", icon=ft.Icons.TABLE_VIEW, height=28,
                style=ft.ButtonStyle(padding=ft.Padding(8, 0, 8, 0), text_style=ft.TextStyle(size=11), side=ft.BorderSide(1, "white24")),
                on_click=lambda _: self.on_export_xlsx() if self.on_export_xlsx else None,
                tooltip="Exportar todas las categorias (estatico)"),
            ft.OutlinedButton("Fórmulas", icon=ft.Icons.FUNCTIONS, height=28,
                style=ft.ButtonStyle(padding=ft.Padding(8, 0, 8, 0), text_style=ft.TextStyle(size=11), side=ft.BorderSide(1, "white24")),
                on_click=self._on_export_formulas,
                tooltip="Exportar categoria activa con formulas vivas"),
        ], spacing=4)

        self._warehouse_badges = WarehouseBadges(
            self.colors, on_toggle_almacen=self._on_toggle_almacen,
        )

        self._ean13_chip = ft.Container(
            content=ft.Text("EAN-13", size=9, color=self.colors["text_muted"], weight=ft.FontWeight.W_600),
            bgcolor=rgba(ft.Colors.WHITE, 0.05),
            border_radius=6,
            padding=ft.Padding(6, 3, 6, 3),
            on_click=self._on_toggle_ean13,
            ink=True,
        )

        self._build_discount_chips()

        self._root = ft.Column([
            ft.Row([
                self._control_categorias.get_control(),
                ft.Container(expand=True),
                self._search_field,
                export_row,
            ], vertical_alignment="center"),
            ft.Row([
                self._warehouse_badges.get_control(),
                self._ean13_chip,
            ], spacing=6, vertical_alignment="center"),
            self._discount_row,
            self._scrollable_body,
            self.pagination.get_control(),
        ], spacing=6, expand=True)

    def _build_discount_chips(self):
        controls = []
        for key, label, numeric in DISCOUNT_DEFS:
            chip = ft.Container(
                content=ft.Text(label, size=9, color=self.colors["text_muted"], weight=ft.FontWeight.W_600),
                bgcolor=rgba(ft.Colors.WHITE, 0.05),
                border_radius=6,
                padding=ft.Padding(6, 3, 6, 3),
                on_click=lambda e, k=key: self._on_toggle_descuento(k),
                ink=True,
            )
            hint = "%" if numeric else "Nombre"
            w = 48 if numeric else 90
            inp = ft.TextField(
                hint_text=hint,
                width=w,
                height=28,
                text_size=11,
                dense=True,
                visible=False,
                bgcolor=rgba(ft.Colors.WHITE, 0.04),
                border_color="white24",
                focused_border_color=self.colors["accent"],
                color=self.colors["text_primary"],
                on_submit=lambda e, k=key: self._on_discount_input_submit(k),
                on_blur=lambda e, k=key: self._on_discount_input_submit(k),
            )
            self._discount_chips[key] = chip
            self._discount_inputs[key] = inp
            controls.append(ft.Row([chip, inp], spacing=3, vertical_alignment="center"))
        self._discount_row = ft.Row(controls, spacing=6, vertical_alignment="center", visible=True)

    def _on_search(self, e):
        self._busqueda = e.control.value.strip().lower()
        self._page = 0
        self._reload()

    def _on_categoria_seleccionada(self, categoria: str | None, productos: list = None):
        if categoria is None:
            self._filtered = []
            self._c_empty.visible = True
            self._table_wrap.visible = False
            self._update_root()
            return
        self._filtered = productos or self.lazy_manager.obtener_productos_por_categoria(categoria)
        toggles = set()
        if self._show_ean13:
            toggles.add("ean13")
        for k, on in self._discount_toggles.items():
            if on:
                toggles.add(k)
        cols = filtrar_columnas(self._filtered, LISTA_PRECIOS_ALL, toggles)
        self._renombrar_custom(cols, categoria)
        if self._table is None:
            self._table = ProductTable(
                self.colors, columns=cols,
                on_cell_edit=self._on_cell_edit_wrapper,
                on_selection_change=self._on_selection_change_wrapper,
                on_sort=self._on_sort,
                on_refresh=self._reload,
                on_header_edit=self._on_header_edit,
            )
        else:
            self._table.set_columns(cols)
        self._cargar_almacenes(self._filtered)
        self._c_empty.visible = False
        self._table_wrap.visible = True
        if self.pagination:
            self.pagination.get_control().visible = True
        self._sync_table()
        self._prefill_all_inputs(categoria)
        self._update_root()

    def _prefill_all_inputs(self, categoria: str):
        for key, on in self._discount_toggles.items():
            if on:
                self._prefill_descuento_input(key)

    def _renombrar_custom(self, cols: list, categoria: str):
        label = self._obtener_label_custom(categoria)
        if not label:
            return
        for c in cols:
            if c["key"] == "_custom":
                c["label"] = label
                break

    def _obtener_label_custom(self, categoria: str) -> str:
        dc = self._obtener_dc(categoria)
        if dc and dc.special_label:
            return dc.special_label
        return ""

    def _obtener_dc(self, categoria: str) -> DescuentosCategoria | None:
        if not self.state:
            return None
        lista_id = self.state.lista_activa
        listas = self.state.listas
        if not lista_id or lista_id not in listas:
            return None
        return listas[lista_id].discounts_by_category.get(categoria)

    def _on_toggle_ean13(self, e):
        self._show_ean13 = not self._show_ean13
        bg = rgba(self.colors["accent"], 0.15) if self._show_ean13 else rgba(ft.Colors.WHITE, 0.05)
        fg = self.colors["accent"] if self._show_ean13 else self.colors["text_muted"]
        side = ft.BorderSide(1, self.colors["accent"]) if self._show_ean13 else ft.BorderSide(1, "transparent")
        self._ean13_chip.bgcolor = bg
        self._ean13_chip.content = ft.Text("EAN-13", size=9, color=fg, weight=ft.FontWeight.W_600)
        self._ean13_chip.border = ft.Border(top=side, bottom=side, left=side, right=side)
        if self._filtered:
            self._on_categoria_seleccionada(self._control_categorias.categoria_activa, self._filtered)
        else:
            self._reload()

    def _on_toggle_descuento(self, key: str):
        on = not self._discount_toggles[key]
        self._discount_toggles[key] = on
        chip = self._discount_chips[key]
        bg = rgba(self.colors["accent"], 0.15) if on else rgba(ft.Colors.WHITE, 0.05)
        fg = self.colors["accent"] if on else self.colors["text_muted"]
        side = ft.BorderSide(1, self.colors["accent"]) if on else ft.BorderSide(1, "transparent")
        chip.bgcolor = bg
        chip.border = ft.Border(top=side, bottom=side, left=side, right=side)
        chip.content = ft.Text(self._get_chip_label(key), size=9, color=fg, weight=ft.FontWeight.W_600)
        inp = self._discount_inputs[key]
        inp.visible = on
        if on and self._filtered:
            self._prefill_descuento_input(key)
        if self._filtered:
            self._on_categoria_seleccionada(self._control_categorias.categoria_activa, self._filtered)
        else:
            inp.update()
            chip.update()

    def _get_chip_label(self, key: str) -> str:
        for k, label, _ in DISCOUNT_DEFS:
            if k == key:
                if key == "_custom" and self._control_categorias and self._control_categorias.categoria_activa:
                    dc = self._obtener_dc(self._control_categorias.categoria_activa)
                    if dc and dc.special_label:
                        return dc.special_label
                return label
        return key

    def _on_discount_input_submit(self, key: str):
        inp = self._discount_inputs.get(key)
        value = (inp.value or "").strip() if inp else ""
        if not value or not self._filtered:
            return
        if key == "_custom":
            self._renombrar_custom_columna(value)
            return
        try:
            val = float(value) / 100.0
        except ValueError:
            return
        if val <= 0:
            return
        cat = self._control_categorias.categoria_activa if self._control_categorias else None
        dc = self._obtener_dc(cat) if cat else None
        if dc is None and cat:
            dc = DescuentosCategoria(category=cat, discounts=[], fixed_discounts=[])
        if key.startswith("_desc"):
            idx = int(key.replace("_desc", "")) - 1
            for p in self._filtered:
                if p.is_fixed_price():
                    continue
                if not p.commercial_discounts:
                    p.commercial_discounts = [0.0] * 4
                while len(p.commercial_discounts) <= idx:
                    p.commercial_discounts.append(0.0)
                p.commercial_discounts[idx] = val
            while len(dc.discounts) <= idx:
                dc.discounts.append(0.0)
            dc.discounts[idx] = val
        elif key == "_rebate":
            for p in self._filtered:
                if not p.is_fixed_price():
                    p.rebate_override = val
            dc.rebate = val
        if dc and cat:
            self._control_categorias.guardar_descuento_categoria(dc)
        self._reload()

    def _renombrar_custom_columna(self, label: str):
        if not label.strip():
            return
        cat = self._control_categorias.categoria_activa if self._control_categorias else None
        if cat:
            dc = self._obtener_dc(cat)
            if dc:
                dc.special_label = label.strip()
                self._control_categorias.guardar_descuento_categoria(dc)
        if self._filtered and cat:
            self._on_categoria_seleccionada(cat, self._filtered)

    def _prefill_descuento_input(self, key: str):
        inp = self._discount_inputs[key]
        cat = self._control_categorias.categoria_activa if self._control_categorias else None
        if not cat:
            return
        dc = self._obtener_dc(cat)
        if not dc:
            return
        if key.startswith("_desc"):
            idx = int(key.replace("_desc", "")) - 1
            if idx < len(dc.discounts) and dc.discounts[idx] > 0:
                inp.value = str(int(dc.discounts[idx] * 100))
            else:
                inp.value = ""
        elif key == "_rebate":
            if dc.rebate > 0:
                inp.value = str(int(dc.rebate * 100))
            else:
                inp.value = ""
        elif key == "_custom":
            inp.value = dc.special_label or ""
        try:
            inp.update()
        except RuntimeError:
            pass

    def _cargar_almacenes(self, productos: list):
        almacenes_count: dict[str, int] = {}
        for p in productos:
            sa = getattr(p, "warehouse_stock", {})
            if isinstance(sa, dict):
                for alm in sa:
                    almacenes_count[alm] = almacenes_count.get(alm, 0) + 1
        if almacenes_count:
            self._warehouse_badges.set_almacenes(almacenes_count)

    def _on_toggle_almacen(self, name: str, visible: bool):
        if self._table:
            self._table.set_extra_almacen(name, visible)
        self._sync_table()
        self._update_root()

    def _on_descuentos_cambiados(self, grupo: str, dc: DescuentosCategoria, productos: list):
        self._filtered = productos
        if self._control_categorias and self._control_categorias.categoria_activa:
            self._on_categoria_seleccionada(self._control_categorias.categoria_activa, self._filtered)
        else:
            self._sync_table()
        self._update_root()

    def _compute_data(self):
        if not self._filtered and self._control_categorias and self._control_categorias.categoria_activa:
            self._filtered = self.lazy_manager.obtener_productos_por_categoria(self._control_categorias.categoria_activa)
        if self._busqueda:
            self._filtered = [p for p in self._filtered if self._busqueda in p.sku.lower() or self._busqueda in p.description.lower()]

    def _sync_controls(self):
        has_data = bool(self._filtered)
        if self._c_empty:
            self._c_empty.visible = not has_data
        if self._table_wrap:
            self._table_wrap.visible = has_data
        if self.pagination:
            self.pagination.get_control().visible = has_data

    def _sync_table(self):
        if not self._table_ctl or not self._table:
            return
        self._table.set_productos(self._filtered)
        self._table_ctl.columns = self._table.build_headers()
        self._table_ctl.rows = self._table.build_rows(self._page, self._page_size)
        try:
            self._table_ctl.update()
        except RuntimeError:
            pass
        if self.pagination:
            self.pagination.set_total(len(self._filtered), self._page, self._page_size)

    def _update_root(self):
        if self._root and self._root.page:
            try:
                self._root.update()
            except RuntimeError:
                pass

    def _reload(self):
        self._compute_data()
        self._sync_controls()
        self._sync_table()
        self._update_root()

    def _on_pag_size_change(self, size: int):
        self._page_size = size
        self._page = 0
        self._reload()

    def _on_page_change(self, page: int):
        self._page = page
        self._sync_table()

    @staticmethod
    def _stock_val(p, alm):
        raw = (p.warehouse_stock or {}).get(alm, 0)
        if isinstance(raw, (list, tuple)):
            return int(raw[0]) if raw else 0
        return int(raw or 0)

    def _on_sort(self, key: str, desc: bool):
        self._sort_column = key
        self._sort_desc = desc
        self._page = 0
        if not self._filtered:
            return
        if key.startswith("alm_"):
            alm = key[4:]
            self._filtered.sort(key=lambda p, a=alm: self._stock_val(p, a), reverse=desc)
        else:
            key_fn = self._sort_key_fn(key)
            if key_fn:
                self._filtered.sort(key=key_fn, reverse=desc)
        self._sync_table()

    @staticmethod
    def _sort_key_fn(key: str):
        def _gd(p, idx):
            return float(p.commercial_discounts[idx]) if p.commercial_discounts and len(p.commercial_discounts) > idx else 0.0

        def _ad(p, idx):
            return float(p.additional_discounts[idx]) if p.additional_discounts and len(p.additional_discounts) > idx else 0.0

        m = {
            "sequence": lambda p: getattr(p, "sequence", 0) or 0,
            "sku": lambda p: p.sku or "",
            "description": lambda p: p.description or "",
            "line": lambda p: p.line or "",
            "cantidad": lambda p: int(p.units_per_box or 0),
            "list_price": lambda p: float(p.list_price or 0),
            "net_price": lambda p: float(p.net_price or 0),
            "price_with_tax": lambda p: float(p.price_with_tax or 0),
            "stock": lambda p: int(p.stock or 0),
            "ean13": lambda p: p.ean13 or "",
            "_sku_cliente": lambda p: p.customer_sku or "",
            "_desc01": lambda p: _gd(p, 0),
            "_desc02": lambda p: _gd(p, 1),
            "_desc03": lambda p: _gd(p, 2),
            "_desc04": lambda p: _gd(p, 3),
            "_rebate": lambda p: float(p.rebate_override or 0),
            "_custom": lambda p: float(p.special_override or 0),
            "_adic01": lambda p: _ad(p, 0),
            "_adic02": lambda p: _ad(p, 1),
            "_adic03": lambda p: _ad(p, 2),
            "_fixed_price": lambda p: float(p.fixed_price or 0),
        }
        return m.get(key)

    def _on_cell_edit_wrapper(self, sku: str, col_key: str, value: str):
        if self.on_cell_edit:
            self.on_cell_edit(sku, col_key, value)

    def _on_selection_change_wrapper(self, selected: set):
        if self.on_selection_change:
            self.on_selection_change(selected)

    def _on_header_edit(self, key: str, value: str, h_type: str, category: str = None):
        val_float = float(value) / 100 if value else 0.0
        if key.startswith("_desc"):
            idx = int(key.replace("_desc", "")) - 1
            for p in self._filtered:
                if p.is_fixed_price():
                    continue
                if not p.commercial_discounts:
                    p.commercial_discounts = [0.0] * 4
                while len(p.commercial_discounts) <= idx:
                    p.commercial_discounts.append(0.0)
                p.commercial_discounts[idx] = val_float
        elif key == "_rebate":
            for p in self._filtered:
                if not p.is_fixed_price():
                    p.rebate_override = val_float
        self._reload()

    def inicializar_categorias(self):
        if self._control_categorias:
            self._control_categorias.refrescar_categorias_disponibles()

    def _on_export_formulas(self, e):
        cat = self._control_categorias.categoria_activa if self._control_categorias else None
        if not cat or not self._filtered:
            return
        dc = self._obtener_dc(cat)
        if not dc:
            dc = DescuentosCategoria(category=cat, discounts=[], fixed_discounts=[])
        if self.on_export_xlsx_formulas:
            self.on_export_xlsx_formulas(self._filtered, cat, dc)
