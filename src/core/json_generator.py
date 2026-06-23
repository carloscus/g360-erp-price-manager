"""JSON export: versioned per-category client backups, perfil_cliente accumulation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.constants import DATA_DIR, MAESTRO_FILE
from src.core.models import Producto, ListaPrecio


def generar_json_maestro(productos: list[Producto], path: Optional[str] = None) -> str:
    p = Path(path) if path else MAESTRO_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "metadata": {
            "version": "2.0.0",
            "generated_at": datetime.now().isoformat(),
            "total_productos": len(productos),
            "formato": "catalogo_maestro",
        },
        "productos": [prod.to_dict() for prod in productos],
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(p)


def generar_json_lista(lista: ListaPrecio, productos: list[Producto], path: Optional[str] = None) -> str:
    p = Path(path) if path else DATA_DIR / f"lista_{lista.id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "metadata": {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "lista_id": lista.id,
            "lista_nombre": lista.name,
            "total_productos": len(productos),
        },
        "lista": lista.to_dict(),
        "productos": [prod.to_dict() for prod in productos],
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(p)


def generar_json_exportacion(productos: list[Producto], nombre: str = "export", path: Optional[str] = None) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_path = DATA_DIR / f"{nombre}_{ts}.json"
    p = Path(path) if path else default_path
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "metadata": {
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "total_productos": len(productos),
            "formato": "exportacion",
        },
        "productos": [prod.to_dict() for prod in productos],
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(p)


def generar_json_cliente(
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
    name = f"{cat}_{cl}_{fecha}.json"

    out_dir = DATA_DIR / "listas" / cliente.strip()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name

    if out.exists():
        stem = out.stem
        v = 1
        while out.exists():
            v += 1
            out = out_dir / f"{stem}_v{v}.json"

    data = {
        "version": "2.0.0",
        "type": "personalizada",
        "cliente": cliente.strip(),
        "categoria": categoria,
        "fecha_generacion": datetime.now().isoformat(),
        "fecha_lista": fecha,
        "total_productos": len(productos),
        "productos": [prod.to_dict() for prod in productos if prod.category == categoria],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(out)


def actualizar_perfil_cliente(
    cliente: str,
    productos: list[Producto],
) -> str:
    cl = cliente.strip()
    out_dir = DATA_DIR / "listas" / cl
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"perfil_{cl.replace(' ', '_').upper()}.json"

    perfil: dict = {"cliente": cl, "especiales": {}}
    if out.exists():
        try:
            raw = json.loads(out.read_text(encoding="utf-8"))
            perfil["especiales"] = raw.get("especiales", {})
        except (json.JSONDecodeError, OSError):
            pass

    for p in productos:
        especiales = {}
        if hasattr(p, "desc_manual") and p.desc_manual:
            especiales["desc_manual"] = p.desc_manual
        if p.is_fixed_price() and p.fixed_price:
            especiales["precio_negociado"] = p.fixed_price
        if p.precio_divergente:
            especiales["precio_divergente"] = True
        if especiales:
            entry = perfil["especiales"].setdefault(p.sku, {})
            entry.update(especiales)
            entry["activo"] = True

    data = {
        "version": "1.0.0",
        "tipo": "perfil_cliente",
        "cliente": cl,
        "ultima_actualizacion": datetime.now().isoformat(),
        "especiales": perfil["especiales"],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(out)
