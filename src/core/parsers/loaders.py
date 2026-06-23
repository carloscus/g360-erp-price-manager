"""File loaders for P2 data: categories, discounts, fixed prices, translators."""

import logging
import openpyxl
from g360_core.common import safe_float as _core_safe_float
from src.core.models import PricingRules
from src.core.parsers.common import detectar_columnas, safe_int, safe_float

logger = logging.getLogger(__name__)


def _dfloat(v) -> float:
    if v is None or str(v).strip() == '':
        return 0.0
    f = _core_safe_float(v)
    return f / 100 if f > 1 else f


def cargar_categorias(path: str, rules: PricingRules) -> dict:
    from src.core.parsers.xls_fallback import leer_xls_fallback
    filas = leer_xls_fallback(path)
    if not filas or len(filas) < 2:
        return {'error': 'No se pudieron leer datos del archivo o está vacío'}

    headers = filas[0]
    cmap = detectar_columnas(headers)

    if "sku" not in cmap:
        return {'error': 'No se detectó columna SKU'}

    # Detectar columna de orden (N°, ORDEN, NRO, etc.)
    seq_col = cmap.get("sequence")
    if seq_col is None:
        for i, h in enumerate(headers):
            if h.strip().upper() in ("N°", "N°."):
                seq_col = i
                break

    total = 0
    for row in filas[1:]:
        if len(row) <= cmap["sku"]:
            continue
        
        sku = str(row[cmap["sku"]] or "").strip()
        if not sku:
            continue

        cat = str(row[cmap["category"]] or "").strip() if "category" in cmap and cmap["category"] < len(row) else ""
        if cat:
            rules.categories[sku] = cat

        ub = safe_int(row[cmap["units_per_box"]] if "units_per_box" in cmap and cmap["units_per_box"] < len(row) else "")
        if ub:
            rules.units_per_box[sku] = ub

        mon = str(row[cmap["currency"]] or "").strip() if "currency" in cmap and cmap["currency"] < len(row) else ""
        if mon:
            rules.currency[sku] = mon

        if seq_col is not None and seq_col < len(row):
            seq_val = safe_int(row[seq_col])
            if seq_val and seq_val > 0:
                rules.sequence[sku] = seq_val

        total += 1

    return {'aplicados': total, 'saltados': 0, 'total': total}


def cargar_descuentos(path: str, rules: PricingRules) -> dict:
    from src.core.parsers.xls_fallback import leer_xls_fallback
    filas = leer_xls_fallback(path)
    if not filas or len(filas) < 2:
        return {'error': 'No se pudieron leer datos del archivo o está vacío'}

    headers = filas[0]
    cmap = detectar_columnas(headers)

    if "sku" not in cmap:
        return {'error': 'No se detectó columna SKU'}

    total = 0
    for row in filas[1:]:
        if len(row) <= cmap["sku"]:
            continue
        sku = str(row[cmap["sku"]] or "").strip()
        if not sku:
            continue

        commercial = []
        adic = []
        rebate = 0.0
        for i in range(1, 11):
            key = f"desc{i}"
            if key not in cmap:
                continue
            idx = cmap[key]
            if idx >= len(row):
                continue
            val = _dfloat(row[idx])
            if val <= 0:
                continue
            if i <= 3:
                commercial.append(val)
            elif i == 4:
                rebate = val
            else:
                adic.append(val)

        if commercial:
            rules.discounts[sku] = commercial
        if rebate > 0:
            rules.rebate_overrides[sku] = rebate
        if adic:
            rules.additional_discounts[sku] = adic
        total += 1

    return {'aplicados': total, 'saltados': 0, 'total': total}


def cargar_precios_fijos(path: str, rules: PricingRules) -> dict:
    from src.core.parsers.xls_fallback import leer_xls_fallback
    filas = leer_xls_fallback(path)
    if not filas or len(filas) < 2:
        return {'error': 'No se pudieron leer datos del archivo o está vacío'}

    headers = filas[0]
    cmap = detectar_columnas(headers)

    if "sku" not in cmap or "fixed_price" not in cmap:
        return {'error': 'No se detectaron columnas requeridas (SKU/Precio Fijo)'}

    total = 0
    for row in filas[1:]:
        max_idx = max(cmap["sku"], cmap["fixed_price"])
        if len(row) <= max_idx:
            continue
        sku = str(row[cmap["sku"]] or "").strip()
        if not sku:
            continue

        pf = safe_float(row[cmap["fixed_price"]])
        if pf > 0:
            reason = str(row[cmap["fixed_reason"]] or "").strip() if "fixed_reason" in cmap and cmap["fixed_reason"] < len(row) else ""
            rules.fixed_prices[sku] = (pf, reason)
        total += 1

    return {'aplicados': total, 'saltados': 0, 'total': total}


def cargar_traductor(path: str) -> dict:
    from src.core.parsers.xls_fallback import leer_xls_fallback
    filas = leer_xls_fallback(path)
    if not filas or len(filas) < 2:
        return {'mapping': {}, 'total': 0}

    headers = filas[0]
    cmap = detectar_columnas(headers)

    if "sku" not in cmap or "customer_sku" not in cmap:
        sku_idx, alt_idx = 0, 1
    else:
        sku_idx, alt_idx = cmap["sku"], cmap["customer_sku"]

    mapping: dict[str, str] = {}
    for row in filas[1:]:
        if len(row) <= max(sku_idx, alt_idx):
            continue
        sku = str(row[sku_idx] or "").strip()
        alt = str(row[alt_idx] or "").strip()
        if sku and alt:
            mapping[sku] = alt

    return {'mapping': mapping, 'total': len(mapping)}
