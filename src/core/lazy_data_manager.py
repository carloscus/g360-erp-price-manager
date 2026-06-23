"""Lazy Data Manager: Carga bajo demanda por categoría usando Pandas.

Este módulo se encarga de mantener los ~14,000 productos en memoria RAM
(vía un DataFrame de Pandas) y solo exponer datos al UI cuando el usuario
selecciona una categoría específica.
"""

from __future__ import annotations
import pandas as pd
from typing import Callable, Optional
from dataclasses import dataclass, field

from src.core.models import Producto, DescuentosCategoria
from src.core.engine.price_engine import evaluar_producto


@dataclass
class CategoriaView:
    """Estado de una categoría cargada bajo demanda."""
    nombre: str
    productos: list[Producto] = field(default_factory=list)
    descuentos: DescuentosCategoria | None = None
    visible: bool = False


class LazyDataManager:
    """Gestor de datos que mantiene todo en memoria pero solo renderiza por categoría."""

    def __init__(self):
        # DataFrame principal con todos los productos (14,000+ filas)
        self._df: pd.DataFrame | None = None
        self._productos: dict[str, Producto] = {}
        self._categorias_disponibles: list[str] = []
        self._categoria_activa: str | None = None
        self._callbacks: dict[str, list[Callable]] = {}

    # ── Carga y gestión de datos ───────────────────────────────────────

    def cargar_productos(self, productos: list[Producto]):
        """Carga inicial de productos en memoria ( DataFrame )."""
        self._productos = {p.sku: p for p in productos}
        
        # Construir DataFrame para operaciones rápidas de Pandas
        if not productos:
            self._df = pd.DataFrame()
            return
        
        data = []
        for p in productos:
            data.append({
                "sku": p.sku,
                "description": p.description,
                "line": p.line,
                "category": p.category,
                "family": p.family,
                "list_price": p.list_price,
                "net_price": p.net_price,
                "price_with_tax": p.price_with_tax,
                "stock": p.stock,
                "stock_status": p.stock_status,
                "units_per_box": p.units_per_box,
                "weight_kg": p.weight_kg,
                "sequence": p.sequence,
                "price_type": p.price_type,
                "fixed_price": p.fixed_price,
                "commercial_discounts": [p.commercial_discounts] if p.commercial_discounts else [[]],
                "rebate_override": p.rebate_override,
                "additional_discounts": [p.additional_discounts] if p.additional_discounts else [[]],
                "special_override": p.special_override,
                "feria_discount": p.feria_discount,
                "evento_discount": p.evento_discount,
            })
        
        self._df = pd.DataFrame(data)
        self._categorias_disponibles = sorted(
            self._df[self._df["category"] != ""]["category"].unique().tolist()
        ) if not self._df.empty else []

    def recargar_producto(self, sku: str, producto: Producto):
        """Actualiza o inserta un producto en el DataFrame."""
        self._productos[sku] = producto
        if self._df is not None and not self._df.empty:
            # Actualizar fila correspondiente
            mask = self._df["sku"] == sku
            if mask.any():
                self._df.loc[mask, "list_price"] = producto.list_price
                self._df.loc[mask, "net_price"] = producto.net_price
                self._df.loc[mask, "price_with_tax"] = producto.price_with_tax
                self._df.loc[mask, "stock"] = producto.stock
                self._df.loc[mask, "stock_status"] = producto.stock_status
                self._df.loc[mask, "category"] = producto.category
            else:
                # Si no existe, agregar nueva fila
                nueva_fila = pd.DataFrame([{
                    "sku": producto.sku,
                    "description": producto.description,
                    "line": producto.line,
                    "category": producto.category,
                    "family": producto.family,
                    "list_price": producto.list_price,
                    "net_price": producto.net_price,
                    "price_with_tax": producto.price_with_tax,
                    "stock": producto.stock,
                    "stock_status": producto.stock_status,
                    "units_per_box": producto.units_per_box,
                    "weight_kg": producto.weight_kg,
                    "sequence": producto.sequence,
                    "price_type": producto.price_type,
                    "fixed_price": producto.fixed_price,
                }])
                self._df = pd.concat([self._df, nueva_fila], ignore_index=True)
            
            # Recalcular categorías disponibles
            self._categorias_disponibles = sorted(
                self._df[self._df["category"] != ""]["category"].unique().tolist()
            )

    # ── Selección y filtrado por categoría ─────────────────────────────

    @property
    def categoria_activa(self) -> str | None:
        return self._categoria_activa

    def seleccionar_categoria(self, categoria: str | None) -> list[Producto]:
        """Activa una categoría y retorna los productos de esa categoría."""
        self._categoria_activa = categoria
        if categoria is None:
            return []
        return self.obtener_productos_por_categoria(categoria)

    def obtener_productos_por_categoria(self, categoria: str) -> list[Producto]:
        """Obtiene los productos de una categoría específica."""
        # Optimización: usar diccionario directamente
        productos_cat = [p for p in self._productos.values() if p.category == categoria]
        return productos_cat

    def obtener_todos_los_productos(self) -> list[Producto]:
        """Retorna todos los productos (para exportación)."""
        return list(self._productos.values())

    @property
    def categorias_disponibles(self) -> list[str]:
        return self._categorias_disponibles.copy()

    # ── Aplicar descuentos por categoría ──────────────────────────────

    def aplicar_descuentos_a_categoria(
        self, 
        categoria: str, 
        descuentos: DescuentosCategoria
    ) -> list[Producto]:
        """Aplica descuentos a todos los productos de una categoría y recalcula."""
        productos = self.obtener_productos_por_categoria(categoria)
        for p in productos:
            p._dc_ref = descuentos
            evaluar_producto(p)
        return productos

    def subscribe(self, event: str, callback: Callable):
        self._callbacks.setdefault(event, []).append(callback)

    def _notify(self, event: str, **kwargs):
        for cb in self._callbacks.get(event, []):
            try:
                cb(**kwargs)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Error en callback %s", event)

    def obtener_estadisticas_categoria(self, categoria: str) -> dict:
        """Stats rápidas para KPIs usando pandas."""
        if self._df is None or self._df.empty:
            return {}
        filtro = self._df["category"] == categoria
        if not filtro.any():
            return {}
        sub = self._df[filtro]
        return {
            "total": len(sub),
            "con_stock": int((sub["stock"] > 0).sum()),
            "agotados": int((sub["stock_status"] == "AGOTADO").sum()),
            "precio_promedio": round(sub["list_price"].mean(), 2) if len(sub) > 0 else 0,
            "precio_max": round(sub["list_price"].max(), 2) if len(sub) > 0 else 0,
        }
