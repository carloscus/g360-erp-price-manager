"""Fallback XLS reader: tries openpyxl, xlrd, then xlrd2 for legacy .xls files."""

from __future__ import annotations

import logging

import csv
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

_logger = logging.getLogger(__name__)


def leer_xls_fallback(path: str) -> Optional[list[list[str]]]:
    path_obj = Path(path)
    if not path_obj.exists():
        return None

    raw = path_obj.read_bytes()
    suffix = path_obj.suffix.lower()

    # Reordenar motores según extensión y bytes mágicos para evitar lags con BeautifulSoup (html)
    # .xlsx/.zip empiezan con PK\x03\x04
    is_zip = raw.startswith(b"PK\x03\x04")
    # .xls tradicional empieza con \xd0\xcf\x11\xe0
    is_xls = raw.startswith(b"\xd0\xcf\x11\xe0")
    
    # Determinar si tiene pinta de ser HTML o XML
    prefix = raw[:500].lower()
    has_html_or_xml = b"<html" in prefix or b"<table" in prefix or b"<?xml" in prefix or b"<xml" in prefix

    # Definimos los motores disponibles
    engines_dict = {
        "html": lambda: _leer_html(raw),
        "openpyxl": lambda: _leer_openpyxl(raw),
        "xlrd": lambda: _leer_xlrd(raw),
        "csv": lambda: _leer_csv(raw),
        "xml_spreadsheet": lambda: _leer_xml_spreadsheet(raw),
    }

    # Orden de preferencia según tipo
    if suffix == ".xlsx" or is_zip:
        order = ["openpyxl", "xml_spreadsheet", "xlrd", "csv", "html"]
    elif suffix == ".xls" or is_xls:
        if has_html_or_xml:
            order = ["html", "xml_spreadsheet", "xlrd", "openpyxl", "csv"]
        else:
            order = ["xlrd", "xml_spreadsheet", "openpyxl", "html", "csv"]
    elif suffix == ".csv":
        order = ["csv", "html", "openpyxl", "xlrd", "xml_spreadsheet"]
    else:
        # Por defecto, poner HTML al final si no tiene pinta de HTML para evitar bs4 overhead
        if has_html_or_xml:
            order = ["html", "xml_spreadsheet", "openpyxl", "xlrd", "csv"]
        else:
            order = ["openpyxl", "xlrd", "csv", "xml_spreadsheet", "html"]

    ultimo_error = None
    for nombre in order:
        fn = engines_dict[nombre]
        try:
            _logger.debug("Intentando motor: %s", nombre)
            resultado = fn()
            if resultado and len(resultado) > 1:
                _logger.debug("Exito con motor %s: %d filas", nombre, len(resultado))
                return resultado
        except Exception as e:
            _logger.debug("Error motor %s: %s", nombre, e)
            ultimo_error = e
            continue

    _logger.error("No se pudo leer el archivo: %s. Ultimo error: %s", path, ultimo_error)
    return None


def leer_xls_all_sheets(path: str) -> dict[str, list[list[str]]]:
    path_obj = Path(path)
    if not path_obj.exists():
        return {}
    raw = path_obj.read_bytes()
    try:
        return _leer_openpyxl_all_sheets(raw)
    except Exception:
        return {}


def _leer_openpyxl_all_sheets(raw: bytes) -> dict[str, list[list[str]]]:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    res = {}
    for ws in wb.worksheets:
        filas = []
        for row in ws.iter_rows(values_only=True):
            filas.append([str(c).strip() if c is not None else "" for c in row])
        res[ws.title] = filas
    wb.close()
    return res


def _leer_openpyxl(raw: bytes) -> Optional[list[list[str]]]:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    filas = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            filas.append([str(c).strip() if c is not None else "" for c in row])
    wb.close()
    return filas


def _leer_xlrd(raw: bytes) -> Optional[list[list[str]]]:
    import xlrd
    wb = xlrd.open_workbook(file_contents=raw)
    filas = []
    for sheet_idx in range(wb.nsheets):
        ws = wb.sheet_by_index(sheet_idx)
        for row_idx in range(ws.nrows):
            filas.append([str(ws.cell_value(row_idx, c)).strip() for c in range(ws.ncols)])
    return filas


def _leer_csv(raw: bytes) -> Optional[list[list[str]]]:
    content = raw.decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(content))
    return [row for row in reader]


def _leer_html(raw: bytes) -> Optional[list[list[str]]]:
    from bs4 import BeautifulSoup
    content = raw.decode("utf-8", errors="replace")
    soup = BeautifulSoup(content, "html.parser")
    table = soup.find("table")
    if not table:
        return None
    filas = []
    for tr in table.find_all("tr"):
        celdas = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if celdas:
            filas.append(celdas)
    return filas


def _leer_xml_spreadsheet(raw: bytes) -> Optional[list[list[str]]]:
    NS = {
        "ss": "urn:schemas-microsoft-com:office:spreadsheet",
        "o": "urn:schemas-microsoft-com:office:office",
        "x": "urn:schemas-microsoft-com:office:excel",
    }
    root = ET.fromstring(raw)
    worksheet = root.find(".//ss:Worksheet", NS)
    if worksheet is None:
        worksheet = root.find(".//Worksheet")
    if worksheet is None:
        return None

    table = worksheet.find(".//ss:Table", NS) or worksheet.find(".//Table")
    if table is None:
        return None

    filas = []
    for row in table.findall(".//ss:Row", NS) or table.findall("Row"):
        celdas = []
        for cell in row.findall(".//ss:Cell", NS) or row.findall("Cell"):
            data = cell.find(".//ss:Data", NS) or cell.find("Data")
            text = data.text.strip() if data is not None and data.text else ""
            celdas.append(text)
        if celdas:
            filas.append(celdas)
    return filas
