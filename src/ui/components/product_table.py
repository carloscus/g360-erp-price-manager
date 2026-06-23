import flet as ft
from src.ui.theme import (
    rgba, format_pen,
    F_SMALL, F_NORMAL, F_TINY
)
from src.ui.theme import accent as _accent, text_primary as _tp, text_muted as _tm, warning as _warn, stock_ok as _sok, stock_bj as _sbj, stock_agotado as _sag


STOCK_COLUMNS = [
    {"key": "stock", "label": "Stock", "width": 105, "format": "stock_badge"},
    {"key": "pre_dispatch", "label": "Predesp", "width": 80, "format": "predesp"},
]

# ── Alineación horizontal de celdas ────────────────────────────
# Cada columna lleva "align": "left" | "center" | "right"
#   left   → texto (descripción, categoría, notas, etc.)
#   center → códigos y numéricos (SKU, N°, stock, descuentos, peso)
#   right  → montos monetarios (precios, P.Neto, P.C/IGV)
# El helper _vt() mapea el string a ft.Alignment(halign, 0) y
# también pasa text_align al ft.Text para consistencia en multilínea.
# Uso en _build_cells:
#   _vt(valor, align=col.get("align", "left"))
# Para celdas especiales (badges, botones, PopupMenuButton),
# se envuelve en ft.Container(alignment=ft.Alignment(ha, 0)).
# ───────────────────────────────────────────────────────────────

BASE_COLUMNS = [
    {"key": "_sel", "label": "", "width": 28},
    {"key": "sequence", "label": "N°", "width": 45, "align": "center"},
    {"key": "sku", "label": "SKU", "width": 85, "align": "center"},
    {"key": "description", "label": "Artículo", "width": 280, "align": "left"},
    {"key": "line", "label": "Línea", "width": 100, "align": "left"},
    {"key": "units_per_box", "label": "U/Bx", "width": 55, "align": "center"},
    {"key": "list_price", "label": "P.Lista", "width": 95, "format": "pen", "align": "right"},
]

DISCOUNT_COLUMNS = [
    {"key": "_d1", "label": "Dto1", "width": 50, "fmt": "disc_com", "col": "d1", "align": "center"},
    {"key": "_d2", "label": "Dto2", "width": 50, "fmt": "disc_com", "col": "d2", "align": "center"},
    {"key": "_d3", "label": "Dto3", "width": 50, "fmt": "disc_com", "col": "d3", "align": "center"},
    {"key": "_rebate", "label": "Rebate", "width": 60, "fmt": "rebate", "align": "center"},
    {"key": "_special", "label": "Esp.", "width": 75, "fmt": "especial", "align": "center"},
]

CALC_COLUMNS = [
    {"key": "net_price", "label": "P.Neto", "width": 95, "format": "pen", "align": "right"},
    {"key": "price_with_tax", "label": "P.C/IGV", "width": 100, "format": "pen_cigv", "align": "right"},
]

ALL_COLUMNS = BASE_COLUMNS + DISCOUNT_COLUMNS + CALC_COLUMNS + STOCK_COLUMNS

INVENTARIO_COLUMNS = [
    {"key": "_sel", "label": "", "width": 28},
    {"key": "sequence", "label": "N°", "width": 45, "align": "center"},
    {"key": "sku", "label": "SKU", "width": 85, "align": "center"},
    {"key": "description", "label": "Artículo", "width": 280, "align": "left"},
    {"key": "line", "label": "Línea", "width": 100, "align": "left"},
    {"key": "category", "label": "Categoría", "width": 110, "align": "left"},
    {"key": "units_per_box", "label": "U/Bx", "width": 55, "align": "center"},
    {"key": "weight_kg", "label": "Peso(kg)", "width": 75, "format": "weight", "align": "center"},
    {"key": "list_price", "label": "P.Lista", "width": 95, "format": "pen", "align": "right"},
    {"key": "_d1", "label": "Dto1", "width": 50, "fmt": "disc_com", "col": "d1", "align": "center"},
    {"key": "_d2", "label": "Dto2", "width": 50, "fmt": "disc_com", "col": "d2", "align": "center"},
    {"key": "_d3", "label": "Dto3", "width": 50, "fmt": "disc_com", "col": "d3", "align": "center"},
    {"key": "_rebate", "label": "Rebate", "width": 60, "fmt": "rebate", "align": "center"},
    {"key": "_special", "label": "Esp.", "width": 75, "fmt": "especial", "align": "center"},
    {"key": "net_price", "label": "P.Neto", "width": 95, "format": "pen", "align": "right"},
    {"key": "price_with_tax", "label": "P.C/IGV", "width": 100, "format": "pen_cigv", "align": "right"},
    {"key": "stock", "label": "Stock", "width": 105, "format": "stock_badge", "align": "center"},
    {"key": "pre_dispatch", "label": "Predesp", "width": 80, "format": "predesp", "align": "center"},
]

LISTA_PRECIOS_EXTRA = [
    {"key": "_sku_cliente",   "label": "SKU Cliente",   "width": 110, "align": "left"},
    {"key": "_desc01",        "label": "D1",             "width": 52,  "align": "center"},
    {"key": "_desc02",        "label": "D2",             "width": 52,  "align": "center"},
    {"key": "_desc03",        "label": "D3",             "width": 52,  "align": "center"},
    {"key": "_desc04",        "label": "D4",             "width": 52,  "align": "center"},
    {"key": "_rebate",        "label": "Reb.",           "width": 52,  "align": "center"},
    {"key": "_custom",        "label": "Pers.",          "width": 60,  "align": "center"},
    {"key": "_adic01",        "label": "F1",             "width": 52,  "align": "center"},
    {"key": "_adic02",        "label": "F2",             "width": 52,  "align": "center"},
    {"key": "_adic03",        "label": "F3",             "width": 52,  "align": "center"},
    {"key": "_fixed_price",   "label": "P.Fijo",         "width": 90,  "align": "right"},
]

# Orden completo: las columnas marcadas conditional=True se muestran solo si tienen datos;
# ean13 es toggleable (se activa/desactiva manualmente como los almacenes).
LISTA_PRECIOS_ALL = [
    {"key": "sequence",       "label": "N°",              "width": 40,  "align": "center"},
    {"key": "sku",            "label": "SKU",             "width": 85,  "align": "center"},
    {"key": "_sku_cliente",   "label": "SKU Cliente",     "width": 110, "align": "left",   "conditional": True},
    {"key": "ean13",          "label": "EAN-13",          "width": 100, "align": "center", "toggleable": True},
    {"key": "description",    "label": "Artículo",        "width": 290, "align": "left"},
    {"key": "line",           "label": "Línea",           "width": 100, "align": "left"},
    {"key": "cantidad",       "label": "U/Bx",            "width": 55,  "align": "center"},
    {"key": "list_price",     "label": "P.Lista",         "width": 90,  "format": "pen",      "align": "right"},
    {"key": "_desc01",        "label": "D1",              "width": 52,  "align": "center",   "toggleable": True},
    {"key": "_desc02",        "label": "D2",              "width": 52,  "align": "center",   "toggleable": True},
    {"key": "_desc03",        "label": "D3",              "width": 52,  "align": "center",   "toggleable": True},
    {"key": "_desc04",        "label": "D4",              "width": 52,  "align": "center",   "toggleable": True},
    {"key": "_rebate",        "label": "Reb.",            "width": 52,  "align": "center",   "toggleable": True},
    {"key": "_custom",        "label": "Pers.",           "width": 60,  "align": "center",   "toggleable": True},
    {"key": "_adic01",        "label": "F1",              "width": 52,  "align": "center",   "conditional": True},
    {"key": "_adic02",        "label": "F2",              "width": 52,  "align": "center",   "conditional": True},
    {"key": "_adic03",        "label": "F3",              "width": 52,  "align": "center",   "conditional": True},
    {"key": "_fixed_price",   "label": "P.Fijo",          "width": 90,  "align": "right",    "conditional": True},
    {"key": "net_price",      "label": "Neto",            "width": 90,  "format": "pen",      "align": "right"},
    {"key": "price_with_tax", "label": "C/IGV",           "width": 90,  "format": "pen_cigv", "align": "right"},
    {"key": "stock",          "label": "Stock",           "width": 70,  "align": "center"},
]

def _incluir_columna(col: dict, productos: list, toggles: set) -> bool:
    key = col["key"]
    if col.get("header_type"):
        return True
    if col.get("toggleable"):
        return key in toggles
    if col.get("conditional"):
        if not productos:
            return False
        for p in productos:
            val = _get_cell_value(p, key)
            if val and val[0] and not (isinstance(val[0], str) and val[0].strip() == ""):
                return True
        return False
    return True

def filtrar_columnas(productos: list, column_defs: list, extra_toggles: set = None) -> list:
    toggles = extra_toggles or set()
    return [c for c in column_defs if _incluir_columna(c, productos, toggles)]

LISTA_PRECIOS_COLUMNS = LISTA_PRECIOS_ALL  # compatibilidad ascendente

CONFIGURACION_COLUMNS = [
    {"key": "sequence",       "label": "N°",              "width": 45,  "align": "center"},
    {"key": "sku",            "label": "SKU",             "width": 85,  "align": "center"},
    {"key": "description",    "label": "Artículo",        "width": 260, "align": "left"},
    {"key": "line",           "label": "Línea",           "width": 100, "align": "left"},
    {"key": "category",       "label": "Categoría",       "width": 110, "align": "left"},
    {"key": "units_per_box",  "label": "U/Bx",            "width": 55,  "align": "center"},
    {"key": "_sku_cliente",   "label": "SKU Cliente",     "width": 110, "align": "left"},
    {"key": "list_price",     "label": "P.Lista",         "width": 95,  "format": "pen",      "align": "right"},
    {"key": "_fixed_price",   "label": "P.Fijo",          "width": 90,  "align": "right"},
    {"key": "net_price",      "label": "P.Neto",          "width": 95,  "format": "pen",      "align": "right"},
]


def _vt(text, size=F_SMALL, color=_tp(), align="left", weight=None, max_lines=None, overflow=None):
    ha = {"left": -1, "center": 0, "right": 1}.get(align, -1)
    return ft.DataCell(ft.Container(
        content=ft.Text(str(text), size=size, color=color, text_align=align,
                      weight=weight, max_lines=max_lines, overflow=overflow),
        alignment=ft.Alignment(ha, 0),
    ))


def _get_cell_value(producto, col_key: str):
    dc = producto._dc_ref
    is_override = False

    if col_key in ("_desc01", "_desc02", "_desc03", "_desc04", "_d1", "_d2", "_d3"):
        idx = {"_desc01": 0, "_desc02": 1, "_desc03": 2, "_desc04": 3, "_d1": 0, "_d2": 1, "_d3": 2}[col_key]
        cat_val = dc.discounts[idx] if dc and dc.discounts and len(dc.discounts) > idx else 0.0
        override = producto.commercial_discounts[idx] if producto.commercial_discounts and len(producto.commercial_discounts) > idx else None
        val = override if override is not None and override > 0 else cat_val
        is_override = override is not None and abs(override - cat_val) > 0.0001
        display = f"{val*100:.0f}%" if val > 0 else ""
        color = _warn() if is_override else (_accent() if val > 0 else _tm())
        return display, color, ft.FontWeight.W_700 if is_override else ft.FontWeight.W_400, is_override

    elif col_key.startswith("_adic"):
        idx = int(col_key.replace("_adic0", "").replace("_adic", "")) - 1
        cat_val = dc.fixed_discounts[idx] if dc and dc.fixed_discounts and len(dc.fixed_discounts) > idx else None
        val = producto.additional_discounts[idx] if producto.additional_discounts and len(producto.additional_discounts) > idx else (
            cat_val if cat_val is not None else 0.0
        )
        is_override = producto.additional_discounts and len(producto.additional_discounts) > idx and (
            cat_val is None or abs(producto.additional_discounts[idx] - (cat_val or 0)) > 0.0001
        )
        display = f"{val*100:.0f}%" if val > 0 else ""
        color = _warn() if is_override else (_accent() if val > 0 else _tm())
        return display, color, ft.FontWeight.W_700 if is_override else ft.FontWeight.W_400, is_override

    elif col_key == "_rebate":
        cat_val = dc.rebate if dc else 0.0
        override = producto.rebate_override if producto.rebate_override > 0 else None
        val = override if override is not None else cat_val
        is_override = override is not None and abs(override - cat_val) > 0.0001
        display = f"{val*100:.0f}%" if val > 0 else ""
        if is_override:
            color = _warn()
        elif val > 0:
            color = _accent()
        else:
            color = _tm()
        return display, color, ft.FontWeight.W_700 if is_override else ft.FontWeight.W_400, is_override

    elif col_key == "_feria":
        val = producto.feria_discount
        display = f"{val*100:.0f}%" if val > 0 else ""
        color = _warn() if val > 0 else _tm()
        return display, color, ft.FontWeight.W_700 if val > 0 else ft.FontWeight.W_400, bool(val > 0)

    elif col_key == "_evento":
        val = producto.evento_discount
        display = f"{val*100:.0f}%" if val > 0 else ""
        color = _warn() if val > 0 else _tm()
        return display, color, ft.FontWeight.W_700 if val > 0 else ft.FontWeight.W_400, bool(val > 0)

    elif col_key == "_fixed_price":
        is_fijo = producto.is_fixed_price()
        display = format_pen(producto.fixed_price) if is_fijo else ""
        color = _warn() if is_fijo else _tm()
        return display, color, ft.FontWeight.W_700 if is_fijo else ft.FontWeight.W_400, is_fijo

    elif col_key in ("_special", "_especial"):
        if dc and dc.special_discount > 0:
            label = dc.special_label or "Otro"
            display = f"{label} {dc.special_discount*100:.0f}%"
            color = _warn()
        else:
            display = ""
            color = _tm()
        return display, color, ft.FontWeight.W_400, False

    elif col_key == "_special_adjust":
        val = producto.special_discount_adjust
        display = f"{val*100:.0f}%" if val > 0 else ""
        color = _warn() if val > 0 else _tm()
        return display, color, ft.FontWeight.W_700 if val > 0 else ft.FontWeight.W_400, bool(val > 0)

    elif col_key == "_special_label":
        val = producto.special_label_override or (dc.special_label if dc else "")
        return val, _tp(), ft.FontWeight.W_400, False

    elif col_key == "_notes":
        return getattr(producto, "notes", ""), _tp(), ft.FontWeight.W_400, False

    return "", _tp(), ft.FontWeight.W_400, False


class CellEditor(ft.Container):
    def __init__(self, producto, col_key: str, initial_value: str, on_commit, on_cancel, colors=None):
        self.producto = producto
        self.col_key = col_key
        self.on_commit = on_commit
        self.on_cancel = on_cancel
        self.colors = colors or {}
        self._text_field = ft.TextField(
            value=initial_value,
            width=70,
            height=26,
            text_size=F_SMALL,
            bgcolor=rgba(self.colors["accent"], 0.1),
            border_color=self.colors["accent"],
            focused_border_color=self.colors["accent"],
            color="white",
            autofocus=True,
            on_submit=self._commit,
        )
        super().__init__(
            content=ft.Row([
                self._text_field,
                ft.IconButton(
                    icon=ft.Icons.CHECK, icon_size=F_NORMAL, icon_color=self.colors["accent"],
                    on_click=lambda e: self._commit(),
                    tooltip="Aplicar",
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE, icon_size=F_NORMAL, icon_color=self.colors["warning"],
                    on_click=lambda e: self._cancel(),
                    tooltip="Cancelar",
                ),
            ], spacing=2),
            bgcolor=rgba(self.colors["accent"], 0.15),
            border=ft.Border.all(1, self.colors["accent"]),
            border_radius=4,
            padding=4,
        )

    def _commit(self, e=None):
        val = self._text_field.value.strip()
        if self.on_commit:
            self.on_commit(self.producto.sku, self.col_key, val)
        if self.on_cancel:
            self.on_cancel()

    def _cancel(self, e=None):
        if self.on_cancel:
            self.on_cancel()


class HeaderEditor(ft.Container):
    def __init__(self, label: str, col_key: str, on_apply, header_type="fixed", initial_value="", category: str | None = None, colors=None):
        self.label_text = label
        self.col_key = col_key
        self.on_apply = on_apply
        self.header_type = header_type
        self.category = category
        self.colors = colors or {}
        
        self.input = ft.TextField(
            value=initial_value,
            hint_text="%" if header_type != "custom" else "Nombre",
            width=50 if header_type != "custom" else 75,
            height=24,
            text_size=10,
            bgcolor=rgba(ft.Colors.WHITE, 0.05),
            border_color="white24",
            focused_border_color=self.colors["accent"],
            color="white",
            content_padding=ft.Padding(4, 0, 4, 0),
            on_submit=self._handle_apply,
            dense=True,
        )

        display_label = label if not category else f"{label}\n({category})"
        self.label_ctl = ft.Text(display_label, size=9, weight=ft.FontWeight.W_800, color=self.colors["text_muted"], text_align="center")

        super().__init__(
            content=ft.Column([
                self.label_ctl,
                self.input,
            ], spacing=2, horizontal_alignment="center", tight=True),
            padding=ft.Padding(4, 4, 4, 4),
            border_radius=4,
        )

    def _handle_apply(self, e):
        val = self.input.value.strip()
        if self.on_apply:
            # Send (key, value, type, category)
            self.on_apply(self.col_key, val, self.header_type, self.category)


class ProductTable:
    def __init__(self, colors: dict, columns: list[dict] | None = None,
                 on_cell_edit=None, on_sort=None, on_selection_change=None, 
                 on_refresh=None, on_header_edit=None):
        self.colors = colors
        self._columns = columns or ALL_COLUMNS
        self.on_cell_edit = on_cell_edit
        self.on_sort = on_sort
        self.on_selection_change = on_selection_change
        self.on_refresh = on_refresh
        self.on_header_edit = on_header_edit
        self._productos = []
        self._sort_column = "sequence"
        self._sort_desc = False
        self._selected: set[str] = set()
        self._extra_almacenes: dict[str, bool] = {}
        self._traductor: dict = {}
        self._editing_cell: tuple = None
        self._editor: CellEditor | None = None
        self._category_options: list[str] | None = None
        self._header_values: dict[str, str] = {}

    def set_header_value(self, key: str, value: str):
        self._header_values[key] = value

    def set_columns(self, columns: list[dict]):
        self._columns = columns

    def set_productos(self, productos: list):
        self._productos = productos

    def set_extra_almacen(self, nombre: str, visible: bool):
        self._extra_almacenes[nombre] = visible

    def set_traductor(self, traductor: dict):
        self._traductor = traductor

    def set_category_options(self, options: list[str]):
        self._category_options = options

    def select_all(self, selected: bool):
        if selected:
            self._selected = {p.sku for p in self._productos}
        else:
            self._selected = set()
        if self.on_selection_change:
            self.on_selection_change(set(self._selected))

    def toggle_selection(self, sku: str):
        if sku in self._selected:
            self._selected.discard(sku)
        else:
            self._selected.add(sku)
        if self.on_selection_change:
            self.on_selection_change(set(self._selected))

    def get_selected(self) -> set:
        return set(self._selected)

    def build_headers(self) -> list[ft.DataColumn]:
        headers = []
        for col in self._columns:
            key = col["key"]
            label = col["label"]
            h_type = col.get("header_type")
            
            if h_type:
                # Interactive Header
                header_ctl = HeaderEditor(
                    label=label,
                    col_key=key,
                    header_type=h_type,
                    initial_value=self._header_values.get(key, ""),
                    on_apply=self.on_header_edit,
                    category=col.get("category"),
                    colors=self.colors,
                )
                headers.append(ft.DataColumn(header_ctl))
                continue

            sortable = key != "_sel"
            sort_icon = None
            is_sorted = self._sort_column == key
            
            if sortable:
                sort_icon = ft.Icons.ARROW_UPWARD if self._sort_desc and is_sorted else ft.Icons.ARROW_DOWNWARD

            content = ft.Row([
                ft.Text(label, size=F_SMALL, weight=ft.FontWeight.W_800, 
                        color=self.colors["text_primary"] if is_sorted else self.colors["text_muted"]),
                ft.Icon(sort_icon, size=12, 
                        color=self.colors["accent"] if is_sorted else "white10" if sortable else "transparent"),
            ], spacing=2, tight=True, alignment="center" if col.get("align") == "center" else "start")

            def make_click(k, s):
                def inner(e):
                    if k == "_sel":
                        return
                    if self._sort_column == k:
                        self._sort_desc = not self._sort_desc
                    else:
                        self._sort_column = k
                        self._sort_desc = False
                    if self.on_sort:
                        self.on_sort(k, self._sort_desc)
                return inner

            header_ctl = ft.Container(
                content=content,
                padding=ft.Padding(8, 6, 8, 6),
                border_radius=6,
                on_click=make_click(key, sortable),
                bgcolor=rgba(self.colors["accent"], 0.08) if is_sorted else "transparent",
                on_hover=lambda e: self._on_header_hover(e),
                ink=True,
            )
            headers.append(ft.DataColumn(header_ctl))

        for alm_name in self._extra_almacenes:
            if self._extra_almacenes[alm_name]:
                key = f"alm_{alm_name}"
                is_sorted = self._sort_column == key
                sort_icon = ft.Icons.ARROW_UPWARD if self._sort_desc and is_sorted else ft.Icons.ARROW_DOWNWARD
                
                headers.append(ft.DataColumn(ft.Container(
                    content=ft.Row([
                        ft.Text(f"Alm.{alm_name}", size=F_SMALL, weight=ft.FontWeight.W_800, 
                                color=self.colors["text_primary"] if is_sorted else self.colors["text_muted"]),
                        ft.Icon(sort_icon, size=12, color=self.colors["accent"] if is_sorted else "white10"),
                    ], spacing=2, tight=True),
                    padding=ft.Padding(8, 6, 8, 6),
                    border_radius=6,
                    on_click=make_click(key, True),
                bgcolor=rgba(self.colors["accent"], 0.08) if is_sorted else "transparent",
                    on_hover=lambda e: self._on_header_hover(e),
                    ink=True,
                )))

        return headers

    def _on_header_hover(self, e):
        if e.data == "true":
            if not e.control.bgcolor or e.control.bgcolor == "transparent":
                e.control.bgcolor = "white10"
        else:
            if e.control.bgcolor == "white10":
                e.control.bgcolor = "transparent"
        e.control.update()

    def build_rows(self, pagina: int = 0, page_size: int = 50) -> list[ft.DataRow]:
        inicio = pagina * page_size
        fin = inicio + page_size
        subset = self._productos[inicio:fin]

        rows = []
        for idx, p in enumerate(subset):
            cells = self._build_cells(p, inicio + idx)
            rows.append(ft.DataRow(cells=cells))

        return rows

    def _build_cells(self, p, row_idx: int) -> list[ft.DataCell]:
        cells = []
        is_precio_fijo = p.is_fixed_price()
        bg_tint = rgba(self.colors["surface_light"], 0.3) if is_precio_fijo else None
        discount_keys = {"_d1", "_d2", "_d3", "_rebate", "_special", "_especial",
                         "_desc01", "_desc02", "_desc03", "_desc04",
                         "_special_adjust", "_feria", "_evento"}
        discount_keys.update(f"_adic{i:02d}" for i in range(1, 11))

        for col in self._columns:
            key = col["key"]
            if key == "_sel":
                cells.append(self._build_selection_cell(p))
            elif key in ("sequence", "sku", "description", "line", "units_per_box"):
                cells.append(self._build_text_cell(p, key, row_idx, col))
            elif key in discount_keys:
                cells.append(self._build_discount_cell(p, key, col, is_precio_fijo, bg_tint))
            elif key == "list_price":
                cells.append(self._build_list_price_cell(p, col))
            elif key == "net_price":
                cells.append(self._build_price_cell(p, key, col, is_precio_fijo))
            elif key == "price_with_tax":
                cells.append(self._build_price_with_tax_cell(p, col, is_precio_fijo))
            elif key == "stock":
                cells.append(self._build_stock_cell(p))
            elif key == "pre_dispatch":
                cells.append(self._build_predesp_cell(p))
            elif key == "ean13":
                cells.append(self._build_ean13_cell(p, col))
            elif key == "cod_alternativo":
                cells.append(self._build_cod_alternativo_cell(p, col))
            elif key in ("_special_label", "_notes", "_sku_cliente", "_custom"):
                attrs = {
                    "_special_label": "special_label_override", 
                    "_notes": "notes", 
                    "_sku_cliente": "customer_sku",
                    "_custom": "special_override"
                }
                attr = attrs[key]
                val = getattr(p, attr, "")
                if key == "_custom":
                    val = f"{val*100:.0f}%" if val and val > 0 else ""
                elif key == "_special_label" and not val and p._dc_ref:
                    val = p._dc_ref.special_label or ""
                cells.append(self._build_inline_text_cell(p, key, val, col))
            elif key == "category":
                cells.append(self._build_category_cell(p, col))
            elif key == "cantidad":
                cells.append(self._build_cantidad_cell(p, col))
            elif key == "weight_kg":
                cells.append(self._build_weight_cell(p, col))
            elif key == "_fixed_price":
                cells.append(self._build_fixed_price_cell(p, col))
            else:
                cells.append(_vt(getattr(p, key, ""), color=self.colors["text_primary"], align=col.get("align", "left")))

        for alm_name in self._extra_almacenes:
            if self._extra_almacenes[alm_name]:
                cells.append(self._build_almacen_cell(p, alm_name))

        return cells

    def _build_selection_cell(self, p) -> ft.DataCell:
        checked = p.sku in self._selected
        return ft.DataCell(ft.Checkbox(
            value=checked,
            on_change=lambda e, sku=p.sku: self.toggle_selection(sku),
            fill_color=rgba(self.colors["accent"], 0.3) if p.sku in self._selected else None,
            check_color=self.colors["accent"],
            scale=0.8,
        ))

    def _build_text_cell(self, p, key: str, row_idx: int, col: dict) -> ft.DataCell:
        mapping = {
            "sequence": (getattr(p, "sequence", row_idx + 1), self.colors["text_muted"], ft.FontWeight.W_400),
            "sku": (getattr(p, "sku", ""), self.colors["accent"], ft.FontWeight.W_400),
            "description": (getattr(p, "description", ""), self.colors["text_primary"], ft.FontWeight.W_400),
            "line": (getattr(p, "line", ""), self.colors["text_muted"], ft.FontWeight.W_400),
            "units_per_box": (getattr(p, "units_per_box", ""), self.colors["text_primary"], ft.FontWeight.W_400),
        }
        val, color, weight = mapping[key]
        kwargs = {}
        if key == "description":
            kwargs["max_lines"] = 2
            kwargs["overflow"] = ft.TextOverflow.ELLIPSIS
        return _vt(val, color=color, weight=weight, align=col.get("align", "center"), **kwargs)

    def _build_discount_cell(self, p, key: str, col: dict, is_precio_fijo: bool, bg_tint) -> ft.DataCell:
        if self._editing_cell == (p.sku, key) and self._editor:
            return ft.DataCell(self._editor)
        display, color, weight, is_override = _get_cell_value(p, key)
        if is_precio_fijo:
            display = "—"
            color = rgba(self.colors["warning"], 0.6)
            weight = ft.FontWeight.W_400
        has_override = is_override and not is_precio_fijo
        cell_bg = rgba(self.colors["accent"], 0.06) if has_override else bg_tint
        cell_content = ft.Container(
            content=ft.Text(display, size=F_SMALL, color=color, weight=weight, text_align="center"),
            bgcolor=cell_bg,
            border_radius=2,
            padding=ft.Padding(0, 1, 0, 1),
            on_click=lambda e, sku=p.sku, k=key, v=display: (
                None if is_precio_fijo else self._show_editor(sku, k, v, e)
            ),
            ink=True,
            alignment=ft.Alignment(0, 0),
        )
        return ft.DataCell(cell_content)

    def _build_list_price_cell(self, p, col: dict) -> ft.DataCell:
        val = getattr(p, "list_price", 0)
        display = format_pen(float(val or 0))
        divergente = getattr(p, "precio_divergente", False)
        if divergente:
            return ft.DataCell(ft.Container(
                content=ft.Row([
                    ft.Container(width=6, height=6, border_radius=3, bgcolor=self.colors["warning"]),
                    ft.Text(display, size=F_SMALL, color=self.colors["text_primary"]),
                ], spacing=3, tight=True),
                alignment=ft.Alignment(1, 0),
            ))
        return _vt(display, color=self.colors["text_primary"], align=col.get("align", "right"))

    def _build_price_cell(self, p, key: str, col: dict, is_precio_fijo: bool) -> ft.DataCell:
        val = getattr(p, key, 0)
        display = format_pen(float(val or 0))
        color = self.colors["warning"] if is_precio_fijo else self.colors["text_primary"]
        weight = ft.FontWeight.W_700 if is_precio_fijo else ft.FontWeight.W_400
        return _vt(display, color=color, align=col.get("align", "right"), weight=weight)

    def _build_price_with_tax_cell(self, p, col: dict, is_precio_fijo: bool) -> ft.DataCell:
        val = getattr(p, "price_with_tax", 0)
        display = format_pen(float(val or 0))
        color = rgba(self.colors["warning"], 0.7) if is_precio_fijo else self.colors["text_muted"]
        return _vt(display, color=color, align=col.get("align", "right"))

    def _build_stock_cell(self, p) -> ft.DataCell:
        # Target SPECIFICALLY 'VES' warehouse for the main Stock column
        almacenes = getattr(p, "warehouse_stock", {})
        ves_data = almacenes.get("VES", 0)
        
        if isinstance(ves_data, (list, tuple)):
            qty = ves_data[0] if len(ves_data) > 0 else 0
            predesp = ves_data[1] if len(ves_data) > 1 else 0
        else:
            qty = ves_data if isinstance(ves_data, (int, float)) else 0
            predesp = 0

        un_bx = getattr(p, "units_per_box", 1)
        display = None
        if un_bx > 1 and qty > 0:
            boxes = qty // un_bx
            rem = qty % un_bx
            display = f"{boxes}/{rem}" if rem else str(boxes)
        elif qty <= 0:
            display = "—"

        status = "OK" if qty > 0 else "AGOTADO"
        return ft.DataCell(self._stock_badge(qty, status, predesp, display))

    def _build_predesp_cell(self, p) -> ft.DataCell:
        val = getattr(p, "pre_dispatch", 0)
        return ft.DataCell(self._predesp_badge(val))

    def _build_ean13_cell(self, p, col: dict) -> ft.DataCell:
        val = getattr(p, "ean13", "")
        visible = val.strip("0")
        if not visible:
            return ft.DataCell(ft.Container(width=col.get("width", 80)))
        chip = ft.Container(
            content=ft.Text(visible, size=F_TINY, color=self.colors["accent"], weight=ft.FontWeight.W_600, text_align="center"),
            bgcolor=rgba(self.colors["accent"], 0.1), border_radius=4,
            padding=ft.Padding(6, 2, 6, 2),
            alignment=ft.Alignment(0, 0),
        )
        return ft.DataCell(chip)

    def _build_cod_alternativo_cell(self, p, col: dict) -> ft.DataCell:
        val = self._traductor.get(p.sku, "")
        return _vt(val, color=self.colors["text_primary"] if val else self.colors["text_muted"], align=col.get("align", "left"))

    def _build_inline_text_cell(self, p, key: str, val: str, col: dict) -> ft.DataCell:
        if self._editing_cell == (p.sku, key) and self._editor:
            return ft.DataCell(self._editor)
        cell_content = ft.Container(
            content=ft.Text(str(val) if val else "", size=F_SMALL,
                          color=self.colors["text_primary"] if val else self.colors["text_muted"]),
            on_click=lambda e, sku=p.sku, k=key, v=str(val): self._show_editor(sku, k, v, e),
            ink=True,
            alignment=ft.Alignment(0, 0),
        )
        return ft.DataCell(cell_content)

    def _build_fixed_price_cell(self, p, col: dict) -> ft.DataCell:
        is_fijo = p.is_fixed_price()
        display = format_pen(p.fixed_price) if is_fijo else ""
        color = self.colors["warning"] if is_fijo else self.colors["text_muted"]
        cell_content = ft.Container(
            content=ft.Text(display, size=F_SMALL, color=color, text_align="center"),
            on_click=lambda e, sku=p.sku: self._show_editor(sku, "fixed_price", str(p.fixed_price or ""), e),
            ink=not is_fijo,
            alignment=ft.Alignment(0, 0),
        )
        return ft.DataCell(cell_content)

    def _build_category_cell(self, p, col: dict) -> ft.DataCell:
        if self._category_options:
            val = getattr(p, "category", "")
            options = [ft.PopupMenuItem(content=ft.Text(opt), on_click=lambda e, v=opt, s=p.sku: self._on_category_selected(s, v)) for opt in self._category_options]
            return ft.DataCell(ft.Container(
                content=ft.PopupMenuButton(
                    content=ft.Text(str(val) if val else "—", size=F_SMALL,
                                    color=self.colors["text_primary"] if val else self.colors["text_muted"]),
                    items=options,
                ),
                alignment=ft.Alignment(0, 0),
            ))
        if self._editing_cell == (p.sku, "category") and self._editor:
            return ft.DataCell(self._editor)
        val = getattr(p, "category", "")
        cell_content = ft.Container(
            content=ft.Text(str(val) if val else "", size=F_SMALL,
                          color=self.colors["text_primary"] if val else self.colors["text_muted"]),
            on_click=lambda e, sku=p.sku, v=str(val): self._show_editor(sku, "category", v, e),
            ink=True,
            alignment=ft.Alignment(0, 0),
        )
        return ft.DataCell(cell_content)

    def _build_cantidad_cell(self, p, col: dict) -> ft.DataCell:
        un_bx = getattr(p, "units_per_box", 1)
        unidad = getattr(p, "unit_of_measure", "UND")
        display = f"{un_bx} {unidad}" if un_bx > 1 else unidad
        return _vt(display, color=self.colors["text_primary"], align=col.get("align", "center"))

    def _build_weight_cell(self, p, col: dict) -> ft.DataCell:
        val = getattr(p, "weight_kg", 0)
        display = f"{float(val or 0):.2f}" if float(val or 0) > 0 else ""
        return _vt(display, color=self.colors["text_primary"] if val else self.colors["text_muted"], align=col.get("align", "center"))

    def _build_almacen_cell(self, p, alm_name: str) -> ft.DataCell:
        almacenes = getattr(p, "warehouse_stock", {})
        raw = almacenes.get(alm_name, 0) if isinstance(almacenes, dict) else 0
        if isinstance(raw, (list, tuple)):
            qty = raw[0] if len(raw) > 0 else 0
            predesp = raw[1] if len(raw) > 1 else 0
        else:
            qty = raw if isinstance(raw, (int, float)) else 0
            predesp = 0
        
        # Dynamic columns show "Available / Pre-dispatch" format as requested
        return ft.DataCell(self._stock_badge(qty, "OK" if qty > 0 else "AGOTADO", predesp, None))

    def _on_category_selected(self, sku: str, category: str):
        if self.on_cell_edit:
            self.on_cell_edit(sku, "category", category)
        if self.on_refresh:
            self.on_refresh()

    def _show_editor(self, sku: str, col_key: str, current_val: str, event):
        self._editing_cell = (sku, col_key)
        p = next((prod for prod in self._productos if prod.sku == sku), None)

        def on_commit(s, k, v):
            if self.on_cell_edit:
                self.on_cell_edit(s, k, v)
            self._close_editor()

        def on_cancel():
            self._close_editor()

        self._editor = CellEditor(p, col_key, current_val, on_commit, on_cancel, colors=self.colors)
        if self.on_refresh:
            self.on_refresh()

    def _close_editor(self):
        self._editing_cell = None
        self._editor = None
        if self.on_refresh:
            self.on_refresh()

    def get_editor(self) -> CellEditor | None:
        return self._editor

    def _stock_badge(self, disponible: int, status: str, pre_dispatch: int = 0, display: str | None = None) -> ft.Container:
        if status == "AGOTADO" or disponible <= 0:
            bg = rgba(self.colors["stock_agotado"], 0.15)
            fg = self.colors["stock_agotado"]
            return ft.Container(
                content=ft.Text("—", size=F_SMALL, color=fg, weight=ft.FontWeight.W_700, text_align="center"),
                bgcolor=bg, border_radius=4, padding=ft.Padding(10, 2, 10, 2),
                width=85, alignment=ft.Alignment(0, 0),
            )
        elif status == "BJ":
            bg = rgba(self.colors["stock_bj"], 0.15)
            fg = self.colors["stock_bj"]
        else:
            bg = rgba(self.colors["stock_ok"], 0.12)
            fg = self.colors["stock_ok"]

        if display:
            # display is "cajas/unidades"
            content = ft.Text(display, size=F_SMALL, color=fg, weight=ft.FontWeight.W_700, text_align="center")
        elif pre_dispatch > 0:
            content = ft.Row([
                ft.Text(str(disponible), size=F_SMALL, color=fg, weight=ft.FontWeight.W_800),
                ft.Text("/", size=F_SMALL, color=self.colors["text_muted"]),
                ft.Text(str(pre_dispatch), size=F_SMALL, color=rgba(self.colors["warning"], 0.8)),
            ], spacing=1, tight=True, alignment="center")
        else:
            content = ft.Text(str(disponible), size=F_SMALL, color=fg, weight=ft.FontWeight.W_700, text_align="center")

        return ft.Container(
            content=content, bgcolor=bg, border_radius=4, padding=ft.Padding(10, 2, 10, 2),
            width=85, alignment=ft.Alignment(0, 0),
        )

    def _predesp_badge(self, value: int) -> ft.Container:
        if value <= 0:
            return ft.Container(
                content=ft.Text("—", size=F_SMALL, color=self.colors["text_muted"], text_align="center"),
                width=42, alignment=ft.Alignment(0, 0),
            )
        return ft.Container(
            content=ft.Text(str(value), size=F_SMALL, color=self.colors["warning"], weight=ft.FontWeight.W_700, text_align="center"),
            bgcolor=rgba(self.colors["warning"], 0.12), border_radius=4, padding=ft.Padding(8, 2, 8, 2),
            width=42, alignment=ft.Alignment(0, 0),
        )

    def get_sort_info(self) -> tuple:
        return self._sort_column, self._sort_desc
