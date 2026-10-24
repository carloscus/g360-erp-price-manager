"""Utilidades de texto y tipos para los parsers.

Sustituyen al paquete `g360-core`, del que este proyecto dependía pero que
nunca incluyó los módulos `common`, `normalizer` ni `field_keywords`. Todo vive
acá para que el repo sea instalable y testeable sin depender de otro repo.

La configuración de alias de columnas se lee de `assets/data/config.json`
(capa 1 del modelo de estandarización): el código no conoce los nombres de
columna del Excel original.
"""

from __future__ import annotations

import json
import re
import unicodedata

from src.core.constants import DATA_DIR

# Campos numéricos enteros.
INT_FIELDS = {"sequence", "stock", "units_per_box", "pre_dispatch", "version"}

# Campos numéricos decimales.
FLOAT_FIELDS = {
    "list_price",
    "fixed_price",
    "net_price",
    "price_with_tax",
    "weight_kg",
    "special_discount",
    "special_discount_adjust",
}

# Descuentos: se guardan como fracción (0.25 = 25%).
DESC_FIELDS = {f"desc{i}" for i in range(1, 11)}

_PUNCTUATION = re.compile(r"[.,°º/\\()\[\]{}_#*'\"]+")
_SPACES = re.compile(r"\s+")


def deaccent(text: str) -> str:
    """Quita tildes y diacríticos.
    @param text - Texto de entrada
    @returns {str} Texto sin marcas diacríticas
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalizar_header(text: str) -> str:
    """Normaliza un encabezado de columna para poder compararlo.
    @param text - Texto de entrada
    @returns {str} Mayúsculas, sin tildes, sin puntuación y con espacios colapsados
    """
    if text is None:
        return ""
    value = deaccent(str(text)).upper()
    value = _PUNCTUATION.sub(" ", value)
    value = _SPACES.sub(" ", value)
    return value.strip()


def match_keyword(value: str, keyword: str) -> bool:
    """Indica si un valor de celda corresponde a un alias de columna.
    La coincidencia es exacta o por prefijo ("COD" dentro de "CÓDIGO").
    @param value - Valor de la celda
    @param keyword - Alias buscado
    @returns {bool}
    """
    normalized_value = normalizar_header(value)
    normalized_keyword = normalizar_header(keyword)

    if not normalized_value or not normalized_keyword:
        return False

    return normalized_value == normalized_keyword or normalized_value.startswith(
        normalized_keyword
    )


def safe_float(value) -> float | None:
    """Convierte un valor de celda a float tolerando separadores y sucios.
    @param value - Valor crudo
    @returns {float|None} El número o None si no se puede convertir
    """
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()

    text = text.replace("%", "").replace(" ", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        head, _, tail = text.partition(",")
        text = text.replace(",", "") if len(tail) == 3 else text.replace(",", ".")

    try:
        number = float(text)
    except ValueError:
        return None

    return -number if negative else number


def safe_int(value) -> int | None:
    """Convierte un valor de celda a int tolerando separadores y sucios.
    @param value - Valor crudo
    @returns {int|None} El entero o None si no se puede convertir
    """
    number = safe_float(value)
    if number is None:
        return None
    return int(round(number))


def load_field_keywords() -> dict[str, list[str]]:
    """Lee los alias de columnas desde la configuración del proyecto.
    @returns {dict[str, list[str]]} Alias por campo canónico
    """
    config_path = DATA_DIR / "config.json"
    if not config_path.exists():
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            return json.load(handle).get("FIELD_KEYWORDS", {}) or {}
    except (OSError, ValueError):
        return {}


def _build_header_aliases(field_keywords: dict[str, list[str]]) -> dict[str, str]:
    """Arma el mapa de encabezado exacto -> campo canónico.
    El primer campo que reclama un alias gana (mismo criterio que el parser).
    @param field_keywords - Alias por campo canónico
    @returns {dict[str, str]}
    """
    aliases: dict[str, str] = {}

    for field, keywords in field_keywords.items():
        for keyword in keywords:
            normalized = normalizar_header(keyword)
            if normalized and normalized not in aliases:
                aliases[normalized] = field

    return aliases


FIELD_KEYWORDS = load_field_keywords()
HEADER_ALIASES = _build_header_aliases(FIELD_KEYWORDS)


def _normalize_percentage(value: str) -> float:
    """Convierte un porcentaje de Excel a fracción (25 -> 0.25).
    @param value - Valor crudo de la celda
    @returns {float} Fracción entre 0 y 1
    """
    text = str(value).strip().replace("%", "").replace(",", ".")

    try:
        number = float(text)
    except ValueError:
        return 0.0

    if number > 1:
        return number / 100.0
    if number == 1:
        # Ambiguo: en planillas de ERP "1" es 1%, no un 100% de descuento.
        return 0.01
    return number


def normalizar_valor(key: str, value) -> object:
    """Normaliza un valor de celda según el tipo del campo canónico.
    @param key - Campo canónico (sku, list_price, desc1, ...)
    @param value - Valor crudo de la celda
    @returns {object} Valor tipado (float, int o str)
    """
    if value is None:
        return "" if key not in INT_FIELDS | FLOAT_FIELDS | DESC_FIELDS else 0

    if key in DESC_FIELDS:
        return _normalize_percentage(value)

    if key in INT_FIELDS:
        number = safe_int(value)
        return 0 if number is None else number

    if key in FLOAT_FIELDS:
        number = safe_float(value)
        return 0.0 if number is None else number

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


__all__ = [
    "deaccent",
    "normalizar_header",
    "match_keyword",
    "safe_float",
    "safe_int",
    "normalizar_valor",
    "load_field_keywords",
    "FIELD_KEYWORDS",
    "HEADER_ALIASES",
]
