"""Stock downloader: fetches inventory data from the appweb HTTP endpoint."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import requests

from src.core.constants import S1_URL
from src.core.parsers.xls_fallback import leer_xls_fallback
from src.core.parsers.common import detectar_columnas, safe_int

logger = logging.getLogger(__name__)

_FALLBACK_COL_MAP = {
    "sku": 1, "description": 2, "almacen": 9,
    "stock": 13, "predespacho": 16, "disponible": 18,
}

def _infer_ext(resp: requests.Response) -> str:
    ct = (resp.headers.get("content-type") or "").lower()
    if "spreadsheetml" in ct or "openxmlformats" in ct:
        return ".xlsx"
    if "excel" in ct:
        return ".xls"
    cd = resp.headers.get("content-disposition") or ""
    if ".xlsx" in cd:
        return ".xlsx"
    return ".xls"


def _detect_column_map(filas: list[list[str]]) -> tuple[dict[str, int], int, bool]:
    for i, row in enumerate(filas):
        cmap = detectar_columnas(row)
        if cmap.get("sku") is not None and cmap.get("stock") is not None:
            return cmap, i, True

        if "sku" not in cmap and cmap.get("description") is not None and cmap["description"] < 10:
            norm = [str(c).strip().upper() for c in row]
            for j in range(cmap["description"] - 1, -1, -1):
                cell_val = norm[j]
                if cell_val == "" and j not in cmap.values():
                    cmap["sku"] = j
                    break

            has_warehouse = ("almacen" in cmap) or ("warehouse" in cmap)
            if cmap.get("sku") is not None and has_warehouse:
                if "almacen" not in cmap and "warehouse" in cmap:
                    cmap["almacen"] = cmap["warehouse"]
                fb = _FALLBACK_COL_MAP
                if cmap.get("stock") is None:
                    cmap["stock"] = fb["stock"]
                if cmap.get("predespacho") is None:
                    cmap["predespacho"] = fb.get("predespacho")
                if cmap.get("disponible") is None:
                    cmap["disponible"] = fb.get("disponible")
                return cmap, i, True

    return dict(_FALLBACK_COL_MAP), 10, False


def _parse_stock(path: str) -> dict[str, dict]:
    filas = leer_xls_fallback(path)
    if not filas:
        return {}
    col_map, header_row, _ = _detect_column_map(filas)
    max_col = max(col_map.values()) if col_map else 10

    resultado: dict[str, dict] = {}
    last_sku, last_desc = "", ""

    for row in filas[header_row + 1:]:
        if len(row) < max_col + 1:
            continue
        r_sku = str(row[col_map["sku"]] or "").strip().lstrip("'")

        r_desc = str(row[col_map.get("description", 2)] or "").strip()
        r_sku_upper = r_sku.upper()
        if r_sku_upper in ("TOTAL", "SUBTOTAL", "TOTAL GENERAL"):
            last_sku = ""
            continue
        if r_sku and r_sku_upper not in (".", "ARTÍCULO", "ARTICULO"):
            last_sku = r_sku
            last_desc = r_desc
        if not last_sku:
            continue

        stock = safe_int(row[col_map["stock"]])
        pred = safe_int(row[col_map.get("predespacho", 11)])
        disp = safe_int(row[col_map.get("disponible", 12)])
        alm_name = ""
        if "almacen" in col_map and col_map["almacen"] < len(row):
            alm_name = str(row[col_map["almacen"]] or "").strip()

        if last_sku not in resultado:
            resultado[last_sku] = {
                "stock": 0, "predespacho": 0, "disponible": 0,
                "description": last_desc, "almacenes": {},
            }
        resultado[last_sku]["stock"] += stock
        resultado[last_sku]["predespacho"] += pred
        resultado[last_sku]["disponible"] += disp

        if alm_name:
            alm_key = alm_name.upper()
            if alm_key not in resultado[last_sku]["almacenes"]:
                resultado[last_sku]["almacenes"][alm_key] = [0, 0]
            resultado[last_sku]["almacenes"][alm_key][0] += disp
            resultado[last_sku]["almacenes"][alm_key][1] += pred

    return resultado


def download_stock() -> dict[str, dict] | None:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(S1_URL, headers=headers, timeout=120)
        resp.raise_for_status()
        logger.info("Stock response: %s, %d bytes", resp.status_code, len(resp.content))

        suffix = _infer_ext(resp)
        logger.info("Stock file extension: %s", suffix)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            return _parse_stock(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as ex:
        logger.error(f"[StockDownloader] Error: {ex}")
        return None


def parse_stock_from_file(path: str) -> dict[str, dict] | None:
    try:
        return _parse_stock(path)
    except Exception as ex:
        logger.error(f"[StockDownloader] Error parsing file: {ex}")
        return None
