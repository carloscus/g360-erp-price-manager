"""Shared parser utilities: column detection, safe type conversion, header normalization."""

from g360_core.common import (
    normalizar_header,
    deaccent,
    match_keyword,
    HEADER_ALIASES,
    safe_float,
    safe_int,
)


def detectar_columnas(headers: list[str]) -> dict[str, int]:
    from pathlib import Path
    import json
    from src.core.constants import DATA_DIR
    
    field_keywords = {}
    config_path = DATA_DIR / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                field_keywords = config_data.get("FIELD_KEYWORDS", {})
        except Exception:
            pass

    if not field_keywords:
        from g360_core.field_keywords import FIELD_KEYWORDS as CORE_FIELD_KEYWORDS
        field_keywords = CORE_FIELD_KEYWORDS

    norm = [normalizar_header(h) for h in headers]
    col_map: dict[str, int] = {}
    usados: set[int] = set()

    # Primero probar HEADER_ALIASES (coincidencia exacta normalizada)
    for h_idx, h in enumerate(norm):
        if h_idx in usados:
            continue
        if h in HEADER_ALIASES:
            field = HEADER_ALIASES[h]
            col_map[field] = h_idx
            usados.add(h_idx)

    # Luego FIELD_KEYWORDS con match_keyword
    for field, keywords in field_keywords.items():
        if field in col_map:
            continue
        for kw in keywords:
            kw_upper = kw.upper()
            for i, h in enumerate(norm):
                if i in usados:
                    continue
                if match_keyword(h, kw_upper):
                    col_map[field] = i
                    usados.add(i)
                    break
            if field in col_map:
                break

    return col_map


__all__ = [
    "normalizar_header",
    "deaccent",
    "match_keyword",
    "detectar_columnas",
    "safe_float",
    "safe_int",
]