"""Price engine: applies discount chains, computes net/tax prices, evaluates specials and lot rules."""

from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

from src.core.constants import IGV_RATE
from src.core.models import Producto, PriceType, DescuentosCategoria


def _d(val) -> Decimal:
    return Decimal(str(val))


def _round(val: Decimal, places: int = 2) -> float:
    pattern = "0." + "0" * places
    return float(val.quantize(Decimal(pattern), rounding=ROUND_HALF_UP))


def calcular_cascada_factor(descuentos: list[float]) -> Decimal:
    if not descuentos:
        return Decimal("1.0")
    factor = Decimal("1.0")
    for d in descuentos:
        if d > 0:
            factor *= (Decimal("1.0") - _d(d))
    return factor


def calcular_sum_desc(grupo: list[float]) -> float:
    factor = calcular_cascada_factor(grupo)
    return float(round(Decimal("1.0") - factor, 6))


def calcular_precio_neto(list_price: float, discount_chain: list[float]) -> float:
    if not discount_chain or list_price <= 0:
        return float(list_price)
    factor = calcular_cascada_factor(discount_chain)
    net_price = _d(list_price) * factor
    return _round(net_price, 2)


def calcular_precio_cigv(net_price: float) -> float:
    cigv = _d(net_price) * (Decimal("1.0") + _d(IGV_RATE))
    return _round(cigv, 2)


def calcular_precio_con_lista(
    list_price: float, dc: DescuentosCategoria, adic_override: list[float] | None = None,
) -> dict:
    grupo1 = dc.group1
    grupo2_base = adic_override if adic_override is not None else dc.fixed_discounts
    grupo2 = grupo2_base + ([dc.special_discount] if dc.special_discount > 0 else [])
    
    factor1 = calcular_cascada_factor(grupo1)
    factor2 = calcular_cascada_factor(grupo2)
    
    sum_d1 = float(round(Decimal("1.0") - factor1, 6))
    sum_d2 = float(round(Decimal("1.0") - factor2, 6))
    
    total_factor = factor1 * factor2
    net_price = _d(list_price) * total_factor
    price_with_tax = calcular_precio_cigv(float(net_price))
    
    return {
        "list_price": list_price,
        "group1": grupo1,
        "group2": grupo2,
        "sum_desc01": sum_d1,
        "sum_desc02": sum_d2,
        "factor": float(round(total_factor, 6)),
        "net_price": _round(net_price, 2),
        "price_with_tax": price_with_tax,
    }


def calcular_cascada(list_price: float, discount_chain: list[float]) -> dict:
    if not discount_chain or list_price <= 0:
        return {
            "list_price": list_price,
            "factor": 1.0,
            "descuento_total_pct": 0.0,
            "net_price": float(list_price),
            "price_with_tax": calcular_precio_cigv(list_price),
            "pasos": [],
        }

    pasos = []
    precio_acum = _d(list_price)

    for i, d in enumerate(discount_chain):
        if d > 0:
            desc_pct = _d(d)
            desc_monto = (precio_acum * desc_pct).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            precio_acum = (precio_acum - desc_monto).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            pasos.append({
                "nivel": i + 1,
                "desc_pct": float(desc_pct * 100) if d < 1 else float(desc_pct),
                "desc_monto": float(desc_monto),
                "precio_parcial": float(precio_acum),
            })

    factor = calcular_cascada_factor(discount_chain)
    desc_total_pct = float(round((Decimal("1.0") - factor) * 100, 2))
    net_price = _d(list_price) * factor
    price_with_tax = calcular_precio_cigv(float(net_price))

    return {
        "list_price": list_price,
        "factor": float(round(factor, 6)),
        "descuento_total_pct": desc_total_pct,
        "net_price": _round(net_price, 2),
        "price_with_tax": price_with_tax,
        "pasos": pasos,
    }


def evaluar_producto(producto: Producto) -> Producto:
    if producto.is_fixed_price():
        producto.net_price = round(producto.fixed_price, 2)
        producto.price_with_tax = calcular_precio_cigv(producto.net_price)
        return producto

    producto.price_type = PriceType.NORMAL.value
    dc = producto._dc_ref

    grupo1_comerciales = producto.commercial_discounts if producto.commercial_discounts else (
        list(dc.discounts) if dc and dc.discounts else list(producto.discount_chain) if producto.discount_chain else []
    )
    rebate = producto.rebate_override if producto.rebate_override > 0 else (
        dc.rebate if dc else 0.0
    )
    grupo1 = list(grupo1_comerciales) + ([rebate] if rebate > 0 else [])

    grupo2_adicionales = producto.additional_discounts if producto.additional_discounts else (
        list(dc.fixed_discounts) if dc and dc.fixed_discounts else []
    )
    especial = producto.special_override if producto.special_override > 0 else (
        dc.special_discount if dc else 0.0
    )
    especial_adjust = producto.special_discount_adjust
    feria = producto.feria_discount
    evento = producto.evento_discount
    grupo2 = list(grupo2_adicionales) + ([especial] if especial > 0 else []) + ([especial_adjust] if especial_adjust > 0 else []) + ([feria] if feria > 0 else []) + ([evento] if evento > 0 else [])

    factor1 = calcular_cascada_factor(grupo1)
    factor2 = calcular_cascada_factor(grupo2)
    total_factor = factor1 * factor2

    producto.net_price = _round(_d(producto.list_price) * total_factor, 2)
    producto.price_with_tax = calcular_precio_cigv(producto.net_price)
    return producto


def evaluar_lote(productos: list[Producto]) -> list[Producto]:
    return [evaluar_producto(p) for p in productos]


def resumen_precios(productos: list[Producto]) -> dict:
    total = len(productos)
    con_precio = sum(1 for p in productos if p.list_price > 0 or (p.fixed_price and p.fixed_price > 0))
    tipo_fijo = sum(1 for p in productos if p.price_type == PriceType.FIJO.value)
    tipo_normal = sum(1 for p in productos if p.price_type == PriceType.NORMAL.value)
    sin_precio = total - con_precio
    con_stock = sum(1 for p in productos if p.stock > 0)
    agotados = sum(1 for p in productos if p.stock_status == "AGOTADO")
    bajo_stock = sum(1 for p in productos if p.stock_status == "BJ")

    return {
        "total_skus": total,
        "con_precio": con_precio,
        "sin_precio": sin_precio,
        "tipo_normal": tipo_normal,
        "tipo_fijo": tipo_fijo,
        "con_stock": con_stock,
        "agotados": agotados,
        "bajo_stock": bajo_stock,
    }
