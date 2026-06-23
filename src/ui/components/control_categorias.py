"""Panel de control de categorias con carga bajo demanda (On-Demand).

Este componente gestiona el selector de categorias para la carga
bajo demanda de productos por categoria.
"""

import flet as ft
from typing import Callable

from src.ui.theme import rgba, safe_page
from src.core.lazy_data_manager import LazyDataManager
from src.core.models import DescuentosCategoria


class ControlCategoriasOnDemand:
    """Selector de categorias con carga bajo demanda.
    
    Muestra un dropdown de categorias y al seleccionar una notifica
    a la vista para que cargue los productos correspondientes.
    """

    def __init__(
        self,
        lazy_manager: LazyDataManager,
        colors: dict,
        state=None,
        on_categoria_seleccionada: Callable = None,
        on_descuentos_cambiados: Callable = None,
    ):
        self.lazy_manager = lazy_manager
        self.colors = colors
        self.state = state
        self.on_categoria_seleccionada = on_categoria_seleccionada
        self.on_descuentos_cambiados = on_descuentos_cambiados

        self._categoria_activa: str | None = None
        self._dropdown_categorias: ft.Dropdown | None = None
        self._control: ft.Column | None = None

        self._build()

    # ── Construccion de UI ───────────────────────────────────────────

    def _build(self):
        """Construye los controles principales."""
        self._dropdown_categorias = ft.Dropdown(
            label="Categoria",
            hint_text="Seleccione una categoria",
            options=[],
            width=260,
            height=36,
            text_size=12,
            dense=True,
            bgcolor=rgba(ft.Colors.WHITE, 0.04),
            border_color="white24",
            focused_border_color=self.colors["accent"],
            color=self.colors["text_primary"],
            on_select=self._on_categoria_seleccionada_wrapper,
        )

        self._control = ft.Column([
            self._dropdown_categorias,
        ], spacing=4)

    # ── Manejo de eventos ─────────────────────────────────────────────

    def _on_categoria_seleccionada_wrapper(self, e):
        """Maneja la seleccion de categoria desde el dropdown."""
        categoria = e.control.value
        self.seleccionar_categoria(categoria)

    def seleccionar_categoria(self, categoria: str | None):
        """Selecciona una categoria y activa su modo de edicion."""
        if categoria == self._categoria_activa:
            return

        self._categoria_activa = categoria

        if categoria is None:
            if self.on_categoria_seleccionada:
                self.on_categoria_seleccionada(None)
            return

        if self.on_categoria_seleccionada:
            productos = self.lazy_manager.seleccionar_categoria(categoria)
            self.on_categoria_seleccionada(categoria, productos)

    # ── API publica ──────────────────────────────────────────────────

    def get_control(self) -> ft.Control:
        return self._control

    @property
    def categoria_activa(self) -> str | None:
        return self._categoria_activa

    def refrescar_categorias_disponibles(self):
        """Refresca el dropdown con las categorias desde state (Configuracion)."""
        if self.state and self.state.categorias_activas:
            cats = sorted(self.state.categorias_activas)
        else:
            cats = self.lazy_manager.categorias_disponibles
        opts = [ft.dropdown.Option("", "-- Seleccionar --")] + [
            ft.dropdown.Option(c, c) for c in cats
        ]
        self._dropdown_categorias.options = opts
        if safe_page(self._dropdown_categorias):
            self._dropdown_categorias.update()

    def guardar_descuento_categoria(self, dc: DescuentosCategoria):
        """Persiste los descuentos de una categoria en la lista activa."""
        if not self.state:
            return
        lista_id = self.state.lista_activa
        listas = self.state.listas
        if not lista_id or lista_id not in listas:
            return
        lista = listas[lista_id]
        lista.discounts_by_category[dc.category] = dc
        current = self.state.listas
        current[lista_id] = lista
        self.state.listas = current
