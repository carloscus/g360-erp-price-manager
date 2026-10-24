"""Smart parser: column-agnostic source detection and row-by-row product parsing."""

from __future__ import annotations

from src.core.parsers.text import normalizar_valor
from src.core.models import Producto, ParsedSource


from src.core.parsers.common import detectar_columnas, safe_float, safe_int

_DESC_KEYS = [f"desc{i}" for i in range(1, 11)]


def _extraer_descuentos(row: list[str], col_map: dict[str, int]) -> list[float]:
    descuentos = []
    for key in _DESC_KEYS:
        if key in col_map:
            idx = col_map[key]
            if idx < len(row):
                descuentos.append(normalizar_valor(key, row[idx]))
    return [d for d in descuentos if d > 0]


def parsear_fuente(
    filas: list[list[str]], filename: str, sheet_name: str = ""
) -> ParsedSource:
    if not filas or len(filas) < 2:
        return ParsedSource(
            filename=filename, sheet_name=sheet_name, errores=["Archivo vacío"]
        )

    mejor_col_map: dict[str, int] = {}
    mejor_header_row = 0
    mejor_score = 0

    # Buscamos en las primeras 50 filas para ser más robustos con encabezados de ERP
    for i in range(min(50, len(filas))):
        row = filas[i]
        if not any(c.strip() for c in row):
            continue
        cmap = detectar_columnas(row)
        score = len(cmap)
        if "sku" in cmap:
            score += 5
        if "list_price" in cmap:
            score += 3
        if score > mejor_score:
            mejor_score = score
            mejor_col_map = cmap
            mejor_header_row = i
        if score >= 8:
            break

    if "sku" not in mejor_col_map:
        return ParsedSource(
            filename=filename,
            sheet_name=sheet_name,
            errores=["No se detectó columna SKU"],
        )

    all_headers = filas[mejor_header_row]
    mapeadas = set(mejor_col_map.values())
    no_mapeadas = [
        str(all_headers[i]).strip()
        for i in range(len(all_headers))
        if i not in mapeadas and str(all_headers[i]).strip()
    ]

    productos: list[Producto] = []
    errores: list[str] = []

    for row in filas[mejor_header_row + 1 :]:
        if not any(c and c.strip() for c in row):
            continue

        def _val(field: str) -> str:
            idx = mejor_col_map.get(field)
            if idx is not None and idx < len(row):
                return str(row[idx] or "").strip()
            return ""

        sku_raw = _val("sku")
        if not sku_raw or sku_raw.upper() in ("TOTAL", "SUBTOTAL", "TOTAL GENERAL"):
            continue

        descuentos = _extraer_descuentos(row, mejor_col_map)
        fixed_price = normalizar_valor("fixed_price", _val("fixed_price")) or None
        price_type = "FIJO" if fixed_price and fixed_price > 0 else "NORMAL"

        p = Producto(
            sku=normalizar_valor("sku", sku_raw),
            sequence=normalizar_valor("sequence", _val("sequence"))
            or len(productos) + 1,
            description=normalizar_valor(
                "description", _val("description") or _val("full_name")
            ),
            full_name=normalizar_valor(
                "full_name", _val("full_name") or _val("description")
            ),
            line=normalizar_valor("line", _val("line")),
            category=normalizar_valor("category", _val("category")),
            family=normalizar_valor("family", _val("family")),
            group=normalizar_valor("group", _val("group")),
            units_per_box=normalizar_valor("units_per_box", _val("units_per_box")),
            list_price=normalizar_valor("list_price", _val("list_price")),
            discount_chain=descuentos,
            price_type=price_type,
            fixed_price=fixed_price,
            net_price=normalizar_valor("net_price", _val("net_price")),
            price_with_tax=normalizar_valor("price_with_tax", _val("price_with_tax")),
            stock=normalizar_valor("stock", _val("stock")),
            active=normalizar_valor("active", _val("active")),
            sort_key=_val("sort_key"),
            ean13=normalizar_valor("ean13", _val("ean13")),
            weight_kg=normalizar_valor("weight_kg", _val("weight_kg")),
            customer_sku=normalizar_valor("customer_sku", _val("customer_sku")),
            subcategory=normalizar_valor("subcategory", _val("subcategory")),
        )
        productos.append(p)

    return ParsedSource(
        filename=filename,
        sheet_name=sheet_name,
        total_rows=len(productos),
        columns_detected={k: v for k, v in mejor_col_map.items()},
        columns_unmapped=no_mapeadas,
        productos=productos,
        errores=errores,
    )
