"""Theme constants: colors, typography sizes, utility helpers for G360 design system.
Supports dark/light mode via set_theme() + build_colors_dict()."""

from __future__ import annotations

import flet as ft

# ── Dark Palette ──────────────────────────────────────────────────────
_ACCENT = "#34d399"
_ACCENT_LIGHT = "#34d399"
_ACCENT_DARK = "#059669"
_BG = "#0b1220"
_SURFACE = "#1a2333"
_SURFACE_LIGHT = "#243044"
_TEXT_PRIMARY = "#f0f4f8"
_TEXT_MUTED = "#94a3b8"
_TEXT_SECONDARY = "#cbd5e1"
_SUCCESS = "#22c55e"
_WARNING = "#f59e0b"
_ERROR = "#ef4444"
_INFO = "#3b82f6"
_VIOLET = "#8b5cf6"
_PINK = "#ec4899"
_CYAN = "#06b6d4"
_STOCK_OK = "#34d399"
_STOCK_BJ = "#f59e0b"
_STOCK_AGOTADO = "#ef4444"
_BORDER = "white12"
_BORDER_ALT = "white24"
_GRID_LINE = "white10"

# ── Light Palette ─────────────────────────────────────────────────────
_L_ACCENT = "#059669"
_L_ACCENT_LIGHT = "#34d399"
_L_ACCENT_DARK = "#047857"
_L_BG = "#f1f5f9"
_L_SURFACE = "#ffffff"
_L_SURFACE_LIGHT = "#f8fafc"
_L_TEXT_PRIMARY = "#0f172a"
_L_TEXT_MUTED = "#64748b"
_L_TEXT_SECONDARY = "#475569"
_L_SUCCESS = "#16a34a"
_L_WARNING = "#d97706"
_L_ERROR = "#dc2626"
_L_INFO = "#2563eb"
_L_VIOLET = "#7c3aed"
_L_PINK = "#db2777"
_L_CYAN = "#0891b2"
_L_STOCK_OK = "#16a34a"
_L_STOCK_BJ = "#d97706"
_L_STOCK_AGOTADO = "#dc2626"
_L_BORDER = "black12"
_L_BORDER_ALT = "black24"
_L_GRID_LINE = "black10"

# ── Current mode ──────────────────────────────────────────────────────
_dark_mode = True

def set_theme(dark: bool):
    global _dark_mode
    _dark_mode = dark

def is_dark() -> bool:
    return _dark_mode

def _c(dark_val, light_val):
    return dark_val if _dark_mode else light_val

# ── Dynamic color accessors ───────────────────────────────────────────
def accent(): return _c(_ACCENT, _L_ACCENT)
def accent_light(): return _c(_ACCENT_LIGHT, _L_ACCENT_LIGHT)
def accent_dark(): return _c(_ACCENT_DARK, _L_ACCENT_DARK)
def bg(): return _c(_BG, _L_BG)
def surface(): return _c(_SURFACE, _L_SURFACE)
def surface_light(): return _c(_SURFACE_LIGHT, _L_SURFACE_LIGHT)
def text_primary(): return _c(_TEXT_PRIMARY, _L_TEXT_PRIMARY)
def text_muted(): return _c(_TEXT_MUTED, _L_TEXT_MUTED)
def text_secondary(): return _c(_TEXT_SECONDARY, _L_TEXT_SECONDARY)
def success(): return _c(_SUCCESS, _L_SUCCESS)
def warning(): return _c(_WARNING, _L_WARNING)
def error(): return _c(_ERROR, _L_ERROR)
def info(): return _c(_INFO, _L_INFO)
def violet(): return _c(_VIOLET, _L_VIOLET)
def pink(): return _c(_PINK, _L_PINK)
def cyan(): return _c(_CYAN, _L_CYAN)
def stock_ok(): return _c(_STOCK_OK, _L_STOCK_OK)
def stock_bj(): return _c(_STOCK_BJ, _L_STOCK_BJ)
def stock_agotado(): return _c(_STOCK_AGOTADO, _L_STOCK_AGOTADO)
def border(): return _c(_BORDER, _L_BORDER)
def border_alt(): return _c(_BORDER_ALT, _L_BORDER_ALT)
def grid_line(): return _c(_GRID_LINE, _L_GRID_LINE)

# ── Backward-compat constants (always dark) ──────────────────────────
# These stay as static dark values for code that imports directly.
# New code should use the accessor functions above or build_colors_dict().
BG_DARK = _BG
SURFACE = _SURFACE
SURFACE_LIGHT = _SURFACE_LIGHT
TEXT_PRIMARY = _TEXT_PRIMARY
TEXT_MUTED = _TEXT_MUTED
TEXT_SECONDARY = _TEXT_SECONDARY
ACCENT = _ACCENT
ACCENT_LIGHT = _ACCENT_LIGHT
ACCENT_DARK = _ACCENT_DARK
SUCCESS = _SUCCESS
WARNING = _WARNING
ERROR = _ERROR
INFO = _INFO
VIOLET = _VIOLET
PINK = _PINK
CYAN = _CYAN
STOCK_OK = _STOCK_OK
STOCK_BJ = _STOCK_BJ
STOCK_AGOTADO = _STOCK_AGOTADO
TIPO_NORMAL_COLOR = _ACCENT
TIPO_FIJO_COLOR = _WARNING
LINEA_COLORS = [_ACCENT, _INFO, _VIOLET, _WARNING, _PINK, _CYAN]

# Font Sizes (theme-independent)
F_TINY = 9
F_SMALL = 11
F_NORMAL = 12
F_MEDIUM = 14
F_LARGE = 16
F_TITLE = 18
F_KPI = 22

# Static styles (reference dark constants — use get_styles() for dynamic)
STYLES = {
    "page_title": ft.TextStyle(size=F_TITLE, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
    "section_title": ft.TextStyle(size=F_MEDIUM, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
    "subsection": ft.TextStyle(size=F_NORMAL, weight=ft.FontWeight.W_600, color=TEXT_MUTED),
    "kpi_value": ft.TextStyle(size=F_KPI, weight=ft.FontWeight.W_800, color="white"),
    "kpi_value_sm": ft.TextStyle(size=F_LARGE, weight=ft.FontWeight.W_700, color="white"),
    "kpi_label": ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_500, color=TEXT_MUTED),
    "data_cell": ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_400, color="#e2e8f0"),
    "data_header": ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_700, color=TEXT_MUTED),
    "badge": ft.TextStyle(size=10, weight=ft.FontWeight.W_700, color="white"),
}

def get_styles() -> dict:
    """Theme-aware styles dict."""
    tp = text_primary()
    tm = text_muted()
    w = "white" if _dark_mode else "black"
    dc = "#e2e8f0" if _dark_mode else "#334155"
    return {
        "page_title": ft.TextStyle(size=F_TITLE, weight=ft.FontWeight.W_800, color=tp),
        "section_title": ft.TextStyle(size=F_MEDIUM, weight=ft.FontWeight.W_700, color=tp),
        "subsection": ft.TextStyle(size=F_NORMAL, weight=ft.FontWeight.W_600, color=tm),
        "kpi_value": ft.TextStyle(size=F_KPI, weight=ft.FontWeight.W_800, color=w),
        "kpi_value_sm": ft.TextStyle(size=F_LARGE, weight=ft.FontWeight.W_700, color=w),
        "kpi_label": ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_500, color=tm),
        "data_cell": ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_400, color=dc),
        "data_header": ft.TextStyle(size=F_SMALL, weight=ft.FontWeight.W_700, color=tm),
        "badge": ft.TextStyle(size=10, weight=ft.FontWeight.W_700, color=w),
    }


def build_colors_dict(dark: bool | None = None) -> dict:
    """Build a flat dict of theme colors for injection into views/components."""
    d = _dark_mode if dark is None else dark
    if d:
        return {
            "accent": _ACCENT, "accent_light": _ACCENT_LIGHT, "accent_dark": _ACCENT_DARK,
            "success": _SUCCESS, "warning": _WARNING, "error": _ERROR,
            "info": _INFO, "violet": _VIOLET, "pink": _PINK, "cyan": _CYAN,
            "surface": _SURFACE, "surface_light": _SURFACE_LIGHT, "bg_dark": _BG,
            "border": _BORDER, "border_alt": _BORDER_ALT, "grid_line": _GRID_LINE,
            "text_muted": _TEXT_MUTED, "text_primary": _TEXT_PRIMARY, "text_secondary": _TEXT_SECONDARY,
            "stock_ok": _STOCK_OK, "stock_bj": _STOCK_BJ, "stock_agotado": _STOCK_AGOTADO,
            "tipo_normal": _ACCENT, "tipo_fijo": _WARNING,
        }
    return {
        "accent": _L_ACCENT, "accent_light": _L_ACCENT_LIGHT, "accent_dark": _L_ACCENT_DARK,
        "success": _L_SUCCESS, "warning": _L_WARNING, "error": _L_ERROR,
        "info": _L_INFO, "violet": _L_VIOLET, "pink": _L_PINK, "cyan": _L_CYAN,
        "surface": _L_SURFACE, "surface_light": _L_SURFACE_LIGHT, "bg_dark": _L_BG,
        "border": _L_BORDER, "border_alt": _L_BORDER_ALT, "grid_line": _L_GRID_LINE,
        "text_muted": _L_TEXT_MUTED, "text_primary": _L_TEXT_PRIMARY, "text_secondary": _L_TEXT_SECONDARY,
        "stock_ok": _L_STOCK_OK, "stock_bj": _L_STOCK_BJ, "stock_agotado": _L_STOCK_AGOTADO,
        "tipo_normal": _L_ACCENT, "tipo_fijo": _L_WARNING,
    }


# ── Utility functions ─────────────────────────────────────────────────

_COLOR_MAP = {
    ft.Colors.WHITE: "#ffffff", ft.Colors.BLACK: "#000000",
    "white": "#ffffff", "black": "#000000",
}

def rgba(color: str, opacity: float) -> str:
    hex_color = _COLOR_MAP.get(color, color)
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    if len(hex_color) == 6:
        alpha = int(opacity * 255)
        return f"#{alpha:02x}{hex_color}"
    return color


def get_linea_color(index: int) -> str:
    cols = [accent(), info(), violet(), warning(), pink(), cyan()]
    return cols[index % len(cols)]


def get_stock_color(status: str) -> str:
    return {"OK": stock_ok(), "BJ": stock_bj(), "AGOTADO": stock_agotado()}.get(status, text_muted())


def get_tipo_color(tipo: str) -> str:
    return {"NORMAL": accent(), "FIJO": warning()}.get(tipo, text_muted())


def format_pen(value: float) -> str:
    if value == 0:
        return "S/ 0.00"
    return f"S/ {value:,.2f}"


def format_pct(value: float) -> str:
    if value == 0:
        return ""
    return f"{value:.1f}%"


def format_stock(value: int, status: str = "") -> str:
    if value <= 0:
        return "AGOTADO"
    if status == "BJ":
        return f"BJ ({value})"
    return str(value)


def safe_page(control):
    try:
        return control.page
    except RuntimeError:
        return None
