"""Catalogo Maestro — in-memory catalog with JSON persistence and SKU-level upsert."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.constants import DATA_DIR, MAESTRO_FILE, SNAPSHOT_DIR
from src.core.models import Producto


class CatalogoMaestro:
    """In-memory product catalog with JSON persistence. Supports SKU-level upsert and full reload."""

    def __init__(self, path: Optional[str] = None):
        self._path = Path(path) if path else MAESTRO_FILE
        self.productos: dict[str, Producto] = {}
        self._metadata: dict = {}

    def cargar(self, path: Optional[str] = None) -> int:
        p = Path(path) if path else self._path
        if not p.exists():
            return 0
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._metadata = data.get("metadata", {})
        productos_raw = data.get("productos", data if isinstance(data, list) else [])
        self.productos = {}
        for d in productos_raw:
            prod = Producto.from_dict(d)
            self.productos[prod.sku] = prod
        return len(self.productos)

    def guardar(self, path: Optional[str] = None) -> bool:
        import tempfile
        p = Path(path) if path else self._path
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "metadata": {
                "version": "2.0.0",
                "generated_at": datetime.now().isoformat(),
                "total_productos": len(self.productos),
                **self._metadata,
            },
            "productos": [prod.to_dict() for prod in sorted(self.productos.values(), key=lambda x: x.sku)],
        }
        tmp_path = p.with_suffix(".tmp.json")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._backup_if_exists(p)
            tmp_path.replace(p)
            return True
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    def get(self, sku: str) -> Optional[Producto]:
        return self.productos.get(sku)

    def upsert(self, producto: Producto) -> bool:
        exists = producto.sku in self.productos
        self.productos[producto.sku] = producto
        return not exists

    def delete(self, sku: str) -> bool:
        if sku in self.productos:
            del self.productos[sku]
            return True
        return False

    def buscar(self, query: str, limite: int = 50) -> list[Producto]:
        q = query.upper().strip()
        resultados = []
        for p in self.productos.values():
            if q in p.sku.upper() or q in p.description.upper() or q in p.line.upper():
                resultados.append(p)
                if len(resultados) >= limite:
                    break
        return resultados

    def por_linea(self) -> dict[str, list[Producto]]:
        lineas: dict[str, list[Producto]] = {}
        for p in self.productos.values():
            key = p.line or "SIN_LINEA"
            lineas.setdefault(key, []).append(p)
        return lineas

    def stats(self) -> dict:
        total = len(self.productos)
        con_precio = sum(1 for p in self.productos.values() if p.list_price > 0)
        con_descuento = sum(1 for p in self.productos.values() if p.discount_chain)
        lineas = set(p.line for p in self.productos.values() if p.line)
        return {
            "total": total,
            "con_precio": con_precio,
            "sin_precio": total - con_precio,
            "con_descuento": con_descuento,
            "lineas": sorted(lineas),
            "n_lineas": len(lineas),
        }

    def importar_productos(self, productos: list[Producto], merge: bool = True) -> dict:
        nuevos = 0
        actualizados = 0
        for p in productos:
            if p.sku in self.productos:
                if merge:
                    existing = self.productos[p.sku]
                    for attr in ("description", "full_name", "line", "category", "family",
                                 "group", "ean13", "weight_kg", "list_price", "unit_of_measure",
                                 "currency", "product_type", "subcategory"):
                        new_val = getattr(p, attr, None)
                        if new_val and new_val != getattr(existing, attr, None):
                            setattr(existing, attr, new_val)
                    if p.stock > 0:
                        existing.stock = p.stock
                    if p.units_per_box > 1:
                        existing.units_per_box = p.units_per_box
                    if p.commercial_discounts:
                        existing.commercial_discounts = p.commercial_discounts
                    if p.additional_discounts:
                        existing.additional_discounts = p.additional_discounts
                    if p.rebate_override > 0:
                        existing.rebate_override = p.rebate_override
                else:
                    self.productos[p.sku] = p
                actualizados += 1
            else:
                self.productos[p.sku] = p
                nuevos += 1
        return {"nuevos": nuevos, "actualizados": actualizados, "total": len(self.productos)}

    def _backup_if_exists(self, path: Path):
        if path.exists():
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bk = SNAPSHOT_DIR / f"{path.stem}_{ts}.bak.json"
            path.rename(bk)
            try:
                backups = sorted(
                    [f for f in SNAPSHOT_DIR.glob(f"{path.stem}_*.bak.json")],
                    key=lambda x: x.stat().st_mtime
                )
                if len(backups) > 5:
                    for old_bk in backups[:-5]:
                        old_bk.unlink(missing_ok=True)
            except Exception:
                pass
