"""Maestro Comercial — P1 commercial overrides (categories, units/box) that persist across ERP recargas."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.constants import MAESTRO_COMERCIAL_FILE


class MaestroComercial:
    """P1 commercial overrides (categories, units/box) that persist across ERP recargas."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or MAESTRO_COMERCIAL_FILE
        self._data: dict[str, dict] = {}

    def cargar(self) -> int:
        if not self.path.exists():
            self._data = {}
            return 0
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = raw.get("productos", {})
            return len(self._data)
        except (json.JSONDecodeError, KeyError, OSError):
            self._data = {}
            return 0

    def guardar(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0.0",
            "actualizado": datetime.now().isoformat(),
            "total": len(self._data),
            "productos": self._data,
        }
        tmp = self.path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
            return True
        except OSError:
            return False

    def asignar_categoria(self, sku: str, categoria: str):
        entry = self._data.setdefault(sku, {})
        entry["category"] = categoria
        self._data[sku] = entry

    def asignar_units_per_box(self, sku: str, ub: int):
        entry = self._data.setdefault(sku, {})
        entry["units_per_box"] = ub
        self._data[sku] = entry

    def asignar_estado(self, sku: str, estado: str):
        entry = self._data.setdefault(sku, {})
        entry["estado"] = estado
        self._data[sku] = entry

    def get(self, sku: str) -> dict:
        return self._data.get(sku, {})

    def remover_categoria(self, sku: str):
        entry = self._data.get(sku)
        if entry and "category" in entry:
            del entry["category"]

    def aplicar_a(self, productos: list) -> list:
        for p in productos:
            comercial = self._data.get(p.sku)
            if comercial:
                if "category" in comercial and comercial["category"]:
                    p.category = comercial["category"]
                if "units_per_box" in comercial and comercial["units_per_box"]:
                    p.units_per_box = comercial["units_per_box"]
                if "estado" in comercial and comercial["estado"]:
                    p.estado = comercial["estado"]
        return productos

    def limpiar(self):
        self._data = {}
