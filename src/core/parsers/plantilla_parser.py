import logging
import openpyxl
from src.core.parsers.text import normalizar_valor
from src.core.models import Producto, SkuPendiente
from src.core.parsers.common import detectar_columnas, safe_float, safe_int

logger = logging.getLogger(__name__)


def parsear_plantilla_precios(
    path: str,
) -> tuple[list[Producto], list[SkuPendiente], dict]:
    wb = openpyxl.load_workbook(path, data_only=True)
    productos_data = {}

    if not _parse_productos_sheet(wb, productos_data):
        return [], [], {"error": "Hoja PRODUCTOS malformada"}

    _parse_descuentos_sheet(wb, productos_data)
    _parse_precios_fijos_sheet(wb, productos_data)
    _parse_sku_clientes_sheet(wb, productos_data)

    productos, sku_pendientes = _build_productos_list(productos_data)

    stats = {
        "total": len(productos_data),
        "parseados": len(productos),
        "pendientes": len(sku_pendientes),
    }
    return productos, sku_pendientes, stats


def _parse_productos_sheet(wb, productos_data: dict) -> bool:
    ws_prod = wb["PRODUCTOS"]
    headers_prod = [
        str(ws_prod.cell(1, c).value or "").strip()
        for c in range(1, ws_prod.max_column + 1)
    ]
    cmap_prod = detectar_columnas(headers_prod)
    if "sku" not in cmap_prod:
        logger.error("No se detecto columna SKU en la hoja PRODUCTOS")
        return False

    for r in range(2, ws_prod.max_row + 1):
        sku = _val(ws_prod, r, cmap_prod.get("sku"))
        if not sku:
            continue
        productos_data[sku] = {
            "sku": sku,
            "sequence": safe_int(_val(ws_prod, r, cmap_prod.get("sequence"))),
            "description": _val(ws_prod, r, cmap_prod.get("description"))
            or _val(ws_prod, r, cmap_prod.get("full_name")),
            "ean13": _val(ws_prod, r, cmap_prod.get("ean13")),
            "category": _val(ws_prod, r, cmap_prod.get("category")),
            "line": _val(ws_prod, r, cmap_prod.get("line")),
            "group": _val(ws_prod, r, cmap_prod.get("group")),
            "product_type": _val(ws_prod, r, cmap_prod.get("product_type")),
            "family": _val(ws_prod, r, cmap_prod.get("family")),
            "unit_of_measure": _val(ws_prod, r, cmap_prod.get("unit_of_measure"))
            or "UND",
            "weight_kg": safe_float(_val(ws_prod, r, cmap_prod.get("weight_kg"))),
            "units_per_box": safe_int(_val(ws_prod, r, cmap_prod.get("units_per_box")))
            or 1,
            "list_price": safe_float(_val(ws_prod, r, cmap_prod.get("list_price"))),
            "currency": _val(ws_prod, r, cmap_prod.get("currency")) or "PEN",
            "image_url": _val(ws_prod, r, cmap_prod.get("image_url")),
        }
    return True


def _parse_descuentos_sheet(wb, productos_data: dict):
    if "DESCUENTOS" not in wb.sheetnames:
        return
    ws_desc = wb["DESCUENTOS"]
    headers_desc = [
        str(ws_desc.cell(1, c).value or "").strip()
        for c in range(1, ws_desc.max_column + 1)
    ]
    cmap_desc = detectar_columnas(headers_desc)
    if "sku" not in cmap_desc:
        return

    for r in range(2, ws_desc.max_row + 1):
        sku = _val(ws_desc, r, cmap_desc.get("sku"))
        if not sku or sku not in productos_data:
            continue
        commercial, adic, rebate = _parse_descuento_row(ws_desc, r, cmap_desc)
        productos_data[sku]["_commercial"] = commercial
        productos_data[sku]["_adic"] = adic
        productos_data[sku]["_rebate"] = rebate


def _parse_descuento_row(ws, row: int, cmap: dict) -> tuple:
    commercial = []
    adic = []
    rebate = 0.0
    for i in range(1, 8):
        key = f"desc{i}"
        if key in cmap:
            raw = ws.cell(row, cmap[key] + 1).value
            val = normalizar_valor(key, raw)
            if not val or val <= 0:
                continue
            if i <= 3:
                commercial.append(val)
            elif i == 4:
                rebate = val
            else:
                adic.append(val)
    return commercial, adic, rebate


def _parse_precios_fijos_sheet(wb, productos_data: dict):
    if "PRECIOS_FIJOS" not in wb.sheetnames:
        return
    ws_fijos = wb["PRECIOS_FIJOS"]
    headers_fijos = [
        str(ws_fijos.cell(1, c).value or "").strip()
        for c in range(1, ws_fijos.max_column + 1)
    ]
    cmap_fijos = detectar_columnas(headers_fijos)
    if "sku" not in cmap_fijos:
        return
    for r in range(2, ws_fijos.max_row + 1):
        sku = _val(ws_fijos, r, cmap_fijos.get("sku"))
        if not sku or sku not in productos_data:
            continue
        pf = _val(ws_fijos, r, cmap_fijos.get("fixed_price"))
        if pf:
            productos_data[sku]["_fixed_price"] = safe_float(pf)


def _parse_sku_clientes_sheet(wb, productos_data: dict):
    if "SKU_CLIENTES" not in wb.sheetnames:
        return
    ws_cli = wb["SKU_CLIENTES"]
    headers_cli = [
        str(ws_cli.cell(1, c).value or "").strip()
        for c in range(1, ws_cli.max_column + 1)
    ]
    cmap_cli = detectar_columnas(headers_cli)
    if "sku" not in cmap_cli or "customer_sku" not in cmap_cli:
        return
    for r in range(2, ws_cli.max_row + 1):
        sku = _val(ws_cli, r, cmap_cli.get("sku"))
        if not sku or sku not in productos_data:
            continue
        productos_data[sku]["customer_sku"] = _val(
            ws_cli, r, cmap_cli.get("customer_sku")
        )


def _build_productos_list(productos_data: dict) -> tuple:
    productos = []
    sku_pendientes = []
    for sku, data in productos_data.items():
        try:
            prod = Producto(
                sku=sku,
                sequence=data.get("sequence", 0),
                description=data.get("description", ""),
                full_name=data.get("description", ""),
                ean13=data.get("ean13", ""),
                category=data.get("category", ""),
                line=data.get("line", ""),
                group=data.get("group", ""),
                product_type=data.get("product_type", ""),
                family=data.get("family", ""),
                unit_of_measure=data.get("unit_of_measure", "UND"),
                weight_kg=data.get("weight_kg", 0.0),
                units_per_box=data.get("units_per_box", 1),
                list_price=data.get("list_price", 0.0),
                currency=data.get("currency", "PEN"),
                image_url=data.get("image_url", ""),
            )
            _apply_discount_data(prod, data)
            if data.get("_fixed_price"):
                prod.price_type = "FIJO"
                prod.fixed_price = data["_fixed_price"]
            if data.get("customer_sku"):
                prod.customer_sku = data["customer_sku"]
            productos.append(prod)
        except Exception as ex:
            logger.warning(f"Error parseando SKU {sku}: {ex}")
            sku_pendientes.append(
                SkuPendiente(
                    sku=sku,
                    description=data.get("description", ""),
                    origin="plantilla_precios",
                )
            )
    return productos, sku_pendientes


def _apply_discount_data(prod: Producto, data: dict):
    commercial = data.get("_commercial", [])
    adic = data.get("_adic", [])
    rebate = data.get("_rebate", 0.0)
    if commercial:
        prod.commercial_discounts = commercial
    if adic:
        prod.additional_discounts = adic
    if rebate > 0:
        prod.rebate_override = rebate


def _val(ws, row: int, col_idx: int | None) -> str:
    if col_idx is None:
        return ""
    v = ws.cell(row, col_idx + 1).value
    return str(v).strip() if v is not None else ""
