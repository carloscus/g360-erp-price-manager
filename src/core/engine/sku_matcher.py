"""SKU matcher: cross-references ERP product set with stock data, computes active/inactive status."""

from __future__ import annotations

from src.core.models import Producto, SkuPendiente, StockStatus, ActiveState

STOCK_OK_THRESHOLD = 10
STOCK_BJ_THRESHOLD = 3


def cruzar_stock_con_maestro(
    stock_dict: dict[str, dict],
    maestro: dict[str, Producto],
) -> tuple[list[Producto], list[SkuPendiente]]:
    productos_con_stock: list[Producto] = []
    sku_pendientes: list[SkuPendiente] = []

    for sku, stock_info in stock_dict.items():
        stock_total = stock_info.get("stock", 0) if isinstance(stock_info, dict) else int(stock_info)
        predesp = stock_info.get("predespacho", 0) if isinstance(stock_info, dict) else 0
        disponible = stock_info.get("disponible", max(0, stock_total - predesp)) if isinstance(stock_info, dict) else int(stock_info)

        if sku in maestro:
            prod = Producto.from_dict(maestro[sku].to_dict())
            prod.stock = disponible
            prod.pre_dispatch = predesp
            prod.stock_status = _clasificar_stock(disponible)
            if isinstance(stock_info, dict) and "almacenes" in stock_info:
                prod.warehouse_stock = stock_info["almacenes"]
            productos_con_stock.append(prod)
        else:
            desc = stock_info.get("description", "") if isinstance(stock_info, dict) else ""
            sku_pendientes.append(SkuPendiente(
                sku=sku,
                description=desc,
                origin="appweb_stock",
                stock=stock_total,
            ))

    for sku, prod in maestro.items():
        if sku not in stock_dict:
            p = Producto.from_dict(prod.to_dict())
            p.stock = 0
            p.stock_status = StockStatus.AGOTADO.value
            productos_con_stock.append(p)

    return productos_con_stock, sku_pendientes


def filtrar_con_stock(productos: list[Producto]) -> list[Producto]:
    return [p for p in productos if p.stock > 0]


def filtrar_con_precio(productos: list[Producto]) -> list[Producto]:
    return [p for p in productos if p.list_price > 0 or (p.fixed_price and p.fixed_price > 0)]


def filtrar_activos(productos: list[Producto]) -> list[Producto]:
    return [p for p in productos if p.active != ActiveState.INACT.value]


def depurar_por_capas(
    stock_dict: dict[str, dict],
    maestro: dict[str, Producto],
) -> tuple[list[Producto], list[SkuPendiente], dict]:
    todos, pendientes = cruzar_stock_con_maestro(stock_dict, maestro)

    con_stock = filtrar_con_stock(todos)
    con_precio = filtrar_con_precio(con_stock)
    activos = filtrar_activos(con_precio)

    stats = {
        "total_erp": len(stock_dict),
        "cruzados_maestro": len(todos) - len(pendientes),
        "pendientes": len(pendientes),
        "con_stock": len(con_stock),
        "con_precio": len(con_precio),
        "activos": len(activos),
    }

    return activos, pendientes, stats


def segmentar_por_linea(productos: list[Producto]) -> dict[str, list[Producto]]:
    segmentos: dict[str, list[Producto]] = {}
    for p in productos:
        key = p.line or "SIN_LINEA"
        segmentos.setdefault(key, []).append(p)
    return segmentos


def _clasificar_stock(stock: int) -> str:
    if stock <= 0:
        return StockStatus.AGOTADO.value
    if stock <= STOCK_BJ_THRESHOLD:
        return StockStatus.BJ.value
    return StockStatus.OK.value
