"""Source manager: orchestrates named data sources (maestros), merge/replace cycles."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.constants import DATA_DIR, MAESTRO_FILE, SNAPSHOT_DIR
from src.core.models import (
    FieldDiff,
    ListaPrecio,
    MergeResult,
    Override,
    Producto,
    ParsedSource,
    SkuPendiente,
)
from src.core.parsers.xls_fallback import leer_xls_fallback
from src.core.parsers.smart_parser import parsear_fuente


class SourceManager:
    """Orchestrates named data sources (maestros), manages merge and replace cycles."""

    def __init__(self):
        self.maestro: dict[str, Producto] = {}
        self.listas: dict[str, ListaPrecio] = {}
        self.fuentes_cargadas: list[str] = []

    def cargar_maestro(self, path: Optional[str] = None) -> int:
        p = Path(path) if path else MAESTRO_FILE
        if not p.exists():
            return 0
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        productos_raw = data.get("productos", data if isinstance(data, list) else [])
        self.maestro = {}
        for d in productos_raw:
            prod = Producto.from_dict(d)
            self.maestro[prod.sku] = prod
        return len(self.maestro)

    def guardar_maestro(self, path: Optional[str] = None) -> bool:
        p = Path(path) if path else MAESTRO_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "metadata": {
                "version": "2.0.0",
                "generated_at": datetime.now().isoformat(),
                "total_productos": len(self.maestro),
            },
            "productos": [prod.to_dict() for prod in self.maestro.values()],
        }
        self._backup_if_exists(p)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    def importar_archivo(self, path: str) -> ParsedSource:
        filename = Path(path).name
        filas = leer_xls_fallback(path)
        if not filas:
            return ParsedSource(filename=filename, errores=["No se pudo leer el archivo"])
        return parsear_fuente(filas, filename)

    def merge_al_maestro(self, fuente: ParsedSource) -> MergeResult:
        productos_mergeados: list[Producto] = []
        sku_pendientes: list[SkuPendiente] = []
        conflictos: list[str] = []

        for prod_fuente in fuente.productos:
            if prod_fuente.sku in self.maestro:
                master = self.maestro[prod_fuente.sku]
                merged = self._merge_producto(master, prod_fuente)
                self.maestro[prod_fuente.sku] = merged
                productos_mergeados.append(merged)
            else:
                sku_pendientes.append(SkuPendiente(
                    sku=prod_fuente.sku,
                    description=prod_fuente.description,
                    origin=fuente.filename,
                    detection_date=datetime.now().isoformat(),
                    stock=prod_fuente.stock,
                ))

        if fuente.filename not in self.fuentes_cargadas:
            self.fuentes_cargadas.append(fuente.filename)

        return MergeResult(
            productos=productos_mergeados,
            sku_pendientes=sku_pendientes,
            conflictos=conflictos,
            fuentes_usadas=len(self.fuentes_cargadas),
        )

    def reemplazar_maestro(self, fuente: ParsedSource) -> MergeResult:
        sku_pendientes: list[SkuPendiente] = []
        self.maestro = {}
        for p in fuente.productos:
            self.maestro[p.sku] = p

        if fuente.filename not in self.fuentes_cargadas:
            self.fuentes_cargadas.append(fuente.filename)

        return MergeResult(
            productos=list(self.maestro.values()),
            sku_pendientes=sku_pendientes,
            fuentes_usadas=len(self.fuentes_cargadas),
        )

    def _merge_producto(self, base: Producto, incoming: Producto) -> Producto:
        result = Producto.from_dict(base.to_dict())
        for field in [
            "description", "full_name", "line", "category", "family", "group",
            "units_per_box", "ean13", "weight_kg", "unit_of_measure", "subcategory",
        ]:
            incoming_val = getattr(incoming, field, None)
            base_val = getattr(base, field, None)
            if incoming_val and incoming_val != base_val and not base_val:
                setattr(result, field, incoming_val)

        if incoming.list_price > 0 and base.list_price == 0:
            result.list_price = incoming.list_price

        if incoming.discount_chain and not base.discount_chain:
            result.discount_chain = incoming.discount_chain

        if incoming.stock > 0:
            result.stock = incoming.stock

        return result

    def cargar_listas(self, path: Optional[str] = None) -> int:
        from src.core.constants import LISTAS_FILE
        p = Path(path) if path else LISTAS_FILE
        if not p.exists():
            return 0
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        listas_raw = data.get("listas", data if isinstance(data, list) else [])
        self.listas = {}
        for d in listas_raw:
            lp = ListaPrecio.from_dict(d)
            self.listas[lp.id] = lp
        return len(self.listas)

    def guardar_listas(self, path: Optional[str] = None) -> bool:
        from src.core.constants import LISTAS_FILE
        p = Path(path) if path else LISTAS_FILE
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "metadata": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "total_listas": len(self.listas),
            },
            "listas": [lp.to_dict() for lp in self.listas.values()],
        }
        self._backup_if_exists(p)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    def aplicar_lista(self, lista: ListaPrecio) -> list[Producto]:
        resultado = []
        for sku, master in self.maestro.items():
            prod = Producto.from_dict(master.to_dict())
            if lista.discounts_by_category:
                desc_base = lista.get_discounts_for_category(prod.category or prod.line)
            else:
                desc_base = lista.base_discounts if lista.base_discounts else prod.discount_chain
            if sku in lista.overrides:
                ov = lista.overrides[sku]
                if ov.discounts is not None:
                    desc_base = ov.discounts
                if ov.fixed_price is not None:
                    prod.fixed_price = ov.fixed_price
                    prod.price_type = "FIJO"
            prod.discount_chain = desc_base
            resultado.append(prod)
        return resultado

    @staticmethod
    def _backup_if_exists(path: Path):
        if path.exists():
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bk = SNAPSHOT_DIR / f"{path.stem}_{ts}.bak.json"
            path.rename(bk)
