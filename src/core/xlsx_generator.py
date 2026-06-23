"""XLSX export: standard price list (sheets per category) and per-client per-category files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers
from openpyxl.utils import get_column_letter

from src.core.constants import DATA_DIR
from src.core.models import Producto, DescuentosCategoria
from src.core.engine.price_engine import evaluar_producto


_XLSX_COLUMNS = [
    ("sku",            "SKU",             10, "text"),
    ("description",    "Art\u00edculo",    30, "text"),
    ("ean13",          "EAN13",           14, "text"),
    ("category",       "Categor\u00eda",   14, "text"),
    ("line",           "L\u00ednea",      12, "text"),
    ("units_per_box",  "U/Bx",             6, "int"),
    ("list_price",     "P.Lista",         12, "pen"),
    ("_desc01",        "Dto1 %",           8, "pct"),
    ("_desc02",        "Dto2 %",           8, "pct"),
    ("_desc03",        "Dto3 %",           8, "pct"),
    ("_rebate",        "Rebate %",         8, "pct"),
    ("_feria",         "Feria %",          8, "pct"),
    ("_evento",        "Evento %",         8, "pct"),
    ("_fixed_price",   "P.Fijo",          12, "pen"),
    ("net_price",      "P.Neto",          12, "pen"),
    ("price_with_tax", "P.C/IGV",         12, "pen"),
    ("stock",          "Stock",            8, "int"),
    ("precio_divergente", "Divergente",    8, "text"),
]


_HEADER_FILL = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
_THIN_BORDER = Border(
    left=Side(style="thin", color="BBBBBB"),
    right=Side(style="thin", color="BBBBBB"),
    top=Side(style="thin", color="BBBBBB"),
    bottom=Side(style="thin", color="BBBBBB"),
)
_PCT_THRESHOLD = 0.0001
_DIVERGENT_FILL = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
_ACCENT_FILL = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
_TITLE_FONT = Font(bold=True, color="FFFFFF", size=13)
_SUBTITLE_FONT = Font(bold=True, color="FFFFFF", size=10)
_TOTAL_FILL = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
_TOTAL_FONT = Font(bold=True, size=10)
_ALT_ROW_FILL = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")


def _cell_value(p: Producto, col: str):
    dc = p._dc_ref
    if col in ("_desc01", "_desc02", "_desc03"):
        idx = {"_desc01": 0, "_desc02": 1, "_desc03": 2}[col]
        if p.commercial_discounts and len(p.commercial_discounts) > idx:
            return p.commercial_discounts[idx]
        val = dc.discounts[idx] if dc and dc.discounts and len(dc.discounts) > idx else 0.0
        return val
    if col.startswith("_adic"):
        idx = int(col.replace("_adic0", "").replace("_adic", "")) - 1
        cat_val = dc.fixed_discounts[idx] if dc and dc.fixed_discounts and len(dc.fixed_discounts) > idx else None
        val = p.additional_discounts[idx] if p.additional_discounts and len(p.additional_discounts) > idx else (
            cat_val if cat_val is not None else 0.0
        )
        return val
    if col == "_rebate":
        if p.rebate_override > 0:
            return p.rebate_override
        return dc.rebate if dc else 0.0
    if col == "_feria":
        return p.feria_discount or 0.0
    if col == "_evento":
        return p.evento_discount or 0.0
    if col == "_fixed_price":
        return p.fixed_price if p.is_fixed_price() else 0.0
    if col in ("_special", "_especial"):
        if dc and dc.special_discount > 0:
            return dc.special_discount
        return 0.0
    if col == "precio_divergente":
        return "S\u00cd" if p.precio_divergente else ""
    if col == "ean13":
        raw = getattr(p, col, "")
        return raw if raw and str(raw).strip() not in ("0", "0.0", "") else ""
    return getattr(p, col, "")


def generar_xlsx_lista(
    productos: list[Producto],
    categorias_activas: set[str],
    filename: str = "",
) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = filename or f"lista_precios_{ts}"
    if not name.endswith(".xlsx"):
        name += ".xlsx"
    out = DATA_DIR / name

    wb = Workbook()
    wb.properties.creator = "ccusi"
    wb.properties.description = "Generado por G360"
    wb.remove(wb.active)

    cats = sorted(categorias_activas) if categorias_activas else [""]
    for cat in cats:
        sheet_products = [p for p in productos if p.category == cat] if cat else list(productos)
        if not sheet_products:
            continue

        ws = wb.create_sheet(title=cat[:31] if cat else "SinCategoria")
        _populate_sheet(ws, sheet_products)

    if not wb.sheetnames:
        ws = wb.create_sheet(title="Productos")
        _populate_sheet(ws, productos)

    wb.save(str(out))
    return str(out)


def _populate_sheet(ws, productos: list[Producto]):
    headers = [h[1] for h in _XLSX_COLUMNS]
    keys = [h[0] for h in _XLSX_COLUMNS]
    formats = [h[3] for h in _XLSX_COLUMNS]
    widths = [h[2] for h in _XLSX_COLUMNS]

    for ci, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=ci, value=h)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _THIN_BORDER
        ws.column_dimensions[get_column_letter(ci)].width = widths[ci - 1]

    for ri, prod in enumerate(productos, 2):
        dc = prod._dc_ref
        for ci, key in enumerate(keys, 1):
            raw = _cell_value(prod, key)
            fmt = formats[ci - 1]

            cell = ws.cell(row=ri, column=ci)
            cell.border = _THIN_BORDER
            cell.font = Font(size=10)

            if prod.precio_divergente:
                cell.fill = _DIVERGENT_FILL

            if fmt == "pen":
                cell.value = float(raw or 0)
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal="right")
            elif fmt == "pct":
                val = float(raw or 0)
                cell.value = val if val > _PCT_THRESHOLD else None
                cell.number_format = '0%'
                cell.alignment = Alignment(horizontal="center")
            elif fmt == "int":
                cell.value = int(raw or 0)
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.value = str(raw or "")
                cell.alignment = Alignment(horizontal="left")

    ws.auto_filter.ref = f"A1:{get_column_letter(len(keys))}{len(productos) + 1}"
    ws.freeze_panes = "A2"


def generar_xlsx_cliente(
    productos: list[Producto],
    categoria: str,
    cliente: str,
    fecha: str = "",
) -> str:
    if not fecha:
        fecha = datetime.now().strftime("%d%m%Y")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cl = cliente.strip().upper().replace(" ", "_")
    cat = categoria.strip().upper().replace(" ", "_")
    name = f"{cat}_{cl}_{fecha}.xlsx"

    out_dir = DATA_DIR / "listas" / cliente.strip()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name

    sheet_products = [p for p in productos if p.category == categoria]
    if not sheet_products:
        return ""

    wb = Workbook()
    wb.properties.creator = "ccusi"
    wb.properties.description = "Generado por G360"
    ws = wb.active
    ws.title = categoria[:31]
    _populate_sheet(ws, sheet_products)
    wb.save(str(out))
    return str(out)


def _comercial_display(dc: DescuentosCategoria) -> str:
    """Cadena corta ej: '25-4-2-Reb5' solo descuentos comerciales."""
    parts = [str(int(d * 100)) for d in dc.discounts if d > 0]
    if dc.rebate > 0:
        parts.append(f"Reb{int(dc.rebate * 100)}")
    return "-".join(parts) if parts else "—"


def _style_header_cell(ws, row: int, col: int, value: str, width: int = None):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = _HEADER_FONT
    cell.fill = _ACCENT_FILL
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = _THIN_BORDER
    if width:
        ws.column_dimensions[get_column_letter(col)].width = width
    return cell


def _style_data_cell(ws, row: int, col: int, value, fmt: str = "text", alt: bool = False):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = Font(size=9)
    cell.border = _THIN_BORDER
    if alt:
        cell.fill = _ALT_ROW_FILL
    if fmt == "pen":
        cell.value = float(value or 0)
        cell.number_format = '#,##0.00'
        cell.alignment = Alignment(horizontal="right")
    elif fmt == "pct":
        val = float(value or 0)
        cell.value = val if val > _PCT_THRESHOLD else None
        cell.number_format = '0%'
        cell.alignment = Alignment(horizontal="center")
    elif fmt == "int":
        cell.value = int(value or 0)
        cell.alignment = Alignment(horizontal="center")
    elif fmt == "qty":
        cell.value = int(value or 0)
        cell.alignment = Alignment(horizontal="center")
        cell.font = Font(size=9, color="2196F3")
    else:
        cell.value = str(value or "")
        cell.alignment = Alignment(horizontal="left")
    return cell


def generar_xlsx_categoria_formulas(
    productos: list[Producto],
    categoria: str,
    dc: DescuentosCategoria,
    filename: str = "",
) -> str:
    """Genera XLSX con 2 hojas (Lista + Pedido) con formulas vivas, por categoria."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = filename or f"lista_{categoria}_{ts}"
    if not name.endswith(".xlsx"):
        name += ".xlsx"
    out = DATA_DIR / name

    wb = Workbook()
    wb.properties.creator = "ccusi"
    wb.properties.description = "Generado por G360"
    sheet1 = wb.active
    sheet1.title = f"Lista {categoria}"[:31]

    cat_products = [p for p in productos if p.category == categoria]
    if not cat_products:
        wb.save(str(out))
        return str(out)

    for p in cat_products:
        p._dc_ref = dc
        evaluar_producto(p)

    n = len(cat_products)
    title = _comercial_display(dc)

    # Helpers for effective per-product discount values
    def _gd(p, idx):
        if p.commercial_discounts and len(p.commercial_discounts) > idx and p.commercial_discounts[idx] > 0:
            return p.commercial_discounts[idx]
        return dc.discounts[idx] if dc and len(dc.discounts) > idx else 0.0

    def _ad(p, idx):
        if p.additional_discounts and len(p.additional_discounts) > idx and p.additional_discounts[idx] > 0:
            return p.additional_discounts[idx]
        return dc.fixed_discounts[idx] if dc and len(dc.fixed_discounts) > idx else 0.0

    def _reb(p):
        return p.rebate_override if p.rebate_override > 0 else (dc.rebate if dc else 0.0)

    def _sp(p):
        return p.special_override if p.special_override > 0 else 0.0

    # ── Sheet 1: Lista ────────────────────────────────────────────────
    # Columns: A=N° B=SKU C=Artículo D=Línea E=P.Lista
    #          F=D1 G=D2 H=D3 I=D4 J=Rebate K=F1 L=F2 M=F3 N=Pers.
    #          O=Neto P=C/IGV
    last_col_s1 = 16

    # Row 1: Title
    sheet1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col_s1)
    t = sheet1.cell(row=1, column=1, value=f"{categoria} — Descuentos: {title}")
    t.font = _TITLE_FONT
    t.fill = _ACCENT_FILL
    t.alignment = Alignment(horizontal="center", vertical="center")
    sheet1.row_dimensions[1].height = 30

    # Row 3: Headers
    h1 = ["N°", "SKU", "Artículo", "Línea", "P.Lista",
          "D1", "D2", "D3", "D4", "Rebate",
          "F1", "F2", "F3", "Pers.",
          "Neto", "C/IGV"]
    w1 = [5, 12, 35, 12, 11, 6, 6, 6, 6, 7, 6, 6, 6, 7, 11, 11]
    for ci, h in enumerate(h1, 1):
        _style_header_cell(sheet1, 3, ci, h, w1[ci - 1])

    # Row 4+: Data
    for ri, p in enumerate(cat_products):
        r = ri + 4
        alt = ri % 2 == 1
        is_fijo = p.is_fixed_price()

        _style_data_cell(sheet1, r, 1, ri + 1, "int", alt)
        _style_data_cell(sheet1, r, 2, p.sku, "text", alt)
        _style_data_cell(sheet1, r, 3, p.description, "text", alt)
        _style_data_cell(sheet1, r, 4, p.line, "text", alt)
        _style_data_cell(sheet1, r, 5, p.list_price, "pen", alt)

        # Effective discount values (per-product overrides or DC defaults)
        d1 = _gd(p, 0)
        d2 = _gd(p, 1)
        d3 = _gd(p, 2)
        d4 = _gd(p, 3)
        reb = _reb(p)
        f1 = _ad(p, 0)
        f2 = _ad(p, 1)
        f3 = _ad(p, 2)
        sp = _sp(p)

        _style_data_cell(sheet1, r, 6, d1, "pct", alt)
        _style_data_cell(sheet1, r, 7, d2, "pct", alt)
        _style_data_cell(sheet1, r, 8, d3, "pct", alt)
        _style_data_cell(sheet1, r, 9, d4, "pct", alt)
        _style_data_cell(sheet1, r, 10, reb, "pct", alt)
        _style_data_cell(sheet1, r, 11, f1, "pct", alt)
        _style_data_cell(sheet1, r, 12, f2, "pct", alt)
        _style_data_cell(sheet1, r, 13, f3, "pct", alt)
        _style_data_cell(sheet1, r, 14, sp, "pct", alt)

        if is_fijo:
            # Precio Fijo: no aplican descuentos, valor fijo directo
            _style_data_cell(sheet1, r, 15, p.fixed_price or 0, "pen", alt)
            _style_data_cell(sheet1, r, 16, (p.fixed_price or 0) * 1.18, "pen", alt)
        else:
            # Neto formula: P.Lista * (1-D1) * (1-D2) * (1-D3) * (1-D4) * (1-Reb) * (1-F1) * (1-F2) * (1-F3) * (1-Pers)
            cols_disc = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
            factors = "".join(f"*(1-{c}{r})" for c in cols_disc[1:])  # skip E (P.Lista)
            f_neto = f"=E{r}{factors}"
            cell_o = _style_data_cell(sheet1, r, 15, None, "pen", alt)
            cell_o.value = f_neto

            # C/IGV = Neto * 1.18
            cell_p = _style_data_cell(sheet1, r, 16, None, "pen", alt)
            cell_p.value = f"=O{r}*1.18"

    sheet1.auto_filter.ref = f"A3:{get_column_letter(last_col_s1)}{n + 3}"
    sheet1.freeze_panes = "A4"

    # ── Sheet 2: Pedido ───────────────────────────────────────────────
    sheet2 = wb.create_sheet(title=f"Pedido {categoria}"[:31])

    # Row 1: Totals header — merge cells A1:D1 for the label
    sheet2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)
    t2 = sheet2.cell(row=1, column=1, value="TOTALES")
    t2.font = _TOTAL_FONT
    t2.fill = _TOTAL_FILL
    t2.alignment = Alignment(horizontal="right", vertical="center")
    t2.border = _THIN_BORDER
    total_row_start = 4
    total_row_end = total_row_start + n - 1

    # Header columns
    h2 = ["N°", "SKU", "Artículo", "SKU Cliente", "EAN13", "U/Bx",
          "P.Neto", "P.C/IGV", "Stock", "Cantidad",
          "Total Neto", "Total C/IGV", "Cajas"]
    w2 = [5, 12, 30, 14, 14, 6, 11, 11, 8, 10, 12, 12, 7]

    for ci in range(5, len(h2) + 1):  # skip merged cells 1-4
        cl = get_column_letter(ci)
        if ci in (10, 11, 12, 13):  # Cantidad, Total Neto, Total C/IGV, Cajas
            formula = f"=SUM({cl}{total_row_start}:{cl}{total_row_end})"
            c = sheet2.cell(row=1, column=ci)
            c.value = formula
            c.font = _TOTAL_FONT
            c.fill = _TOTAL_FILL
            c.border = _THIN_BORDER
            if ci == 10:
                c.number_format = '#,##0'
                c.alignment = Alignment(horizontal="center")
            else:
                c.number_format = '#,##0.00'
                c.alignment = Alignment(horizontal="right")
        else:
            _style_header_cell(sheet2, 1, ci, "", w2[ci - 1])

    # Row 3: Headers
    for ci, h in enumerate(h2, 1):
        _style_header_cell(sheet2, 3, ci, h, w2[ci - 1])

    # Row 4+: Data
    for ri, p in enumerate(cat_products):
        r = ri + 4
        alt = ri % 2 == 1
        neto_val = float(p.net_price or 0)
        cigv_val = float(p.price_with_tax or 0)

        _style_data_cell(sheet2, r, 1, ri + 1, "int", alt)
        _style_data_cell(sheet2, r, 2, p.sku, "text", alt)
        _style_data_cell(sheet2, r, 3, p.description, "text", alt)
        _style_data_cell(sheet2, r, 4, p.customer_sku or "", "text", alt)
        _style_data_cell(sheet2, r, 5, p.ean13 if p.ean13 and str(p.ean13).strip() not in ("0", "0.0", "") else "", "text", alt)
        _style_data_cell(sheet2, r, 6, p.units_per_box or 0, "int", alt)
        _style_data_cell(sheet2, r, 7, neto_val, "pen", alt)
        _style_data_cell(sheet2, r, 8, cigv_val, "pen", alt)

        stock_val = getattr(p, "stock", 0) or 0
        _style_data_cell(sheet2, r, 9, int(stock_val), "int", alt)
        _style_data_cell(sheet2, r, 10, 0, "int", alt)  # Cantidad (input)

        _style_data_cell(sheet2, r, 11, None, "pen", alt)
        sheet2.cell(row=r, column=11).value = f"=J{r}*G{r}"

        _style_data_cell(sheet2, r, 12, None, "pen", alt)
        sheet2.cell(row=r, column=12).value = f"=J{r}*H{r}"

        _style_data_cell(sheet2, r, 13, None, "pen", alt)
        sheet2.cell(row=r, column=13).value = f"=IF(J{r}>0, J{r}/F{r}, \"\")"
        sheet2.cell(row=r, column=13).number_format = '#,##0.0'

    sheet2.auto_filter.ref = f"A3:{get_column_letter(len(h2))}{n + 3}"
    sheet2.freeze_panes = "A4"
    sheet2.row_dimensions[1].height = 26

    wb.save(str(out))
    return str(out)
