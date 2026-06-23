"""Reactive application state: signals, computed values, view/page/pagination state."""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional


class AppState:
    def __init__(self):
        self._state: dict[str, Any] = {}
        self._subscribers: dict[str, list[Callable]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        old = self._state.get(key)
        if old == value:
            return
        self._state[key] = value
        self._notify(key)

    def subscribe(self, key: str, callback: Callable):
        self._subscribers.setdefault(key, []).append(callback)

    def unsubscribe(self, key: str, callback: Callable):
        if key in self._subscribers:
            self._subscribers[key] = [cb for cb in self._subscribers[key] if cb != callback]

    def _notify(self, key: str):
        for cb in self._subscribers.get(key, []):
            try:
                cb(self)
            except Exception:
                logging.getLogger(__name__).exception("Error in subscriber for key '%s'", key)

    @property
    def catalogo(self) -> dict:
        return self._state.get("catalogo", {})

    @catalogo.setter
    def catalogo(self, value: dict):
        self.set("catalogo", value)

    @property
    def lista_activa(self) -> Optional[str]:
        return self._state.get("lista_activa")

    @lista_activa.setter
    def lista_activa(self, value: Optional[str]):
        self.set("lista_activa", value)

    @property
    def productos(self) -> list:
        return self._state.get("productos", [])

    @productos.setter
    def productos(self, value: list):
        self.set("productos", value)

    @property
    def productos_p2(self) -> list:
        return self._state.get("productos_p2", [])

    @productos_p2.setter
    def productos_p2(self, value: list):
        self.set("productos_p2", value)

    @property
    def filtro_linea(self) -> str:
        return self._state.get("filtro_linea", "")

    @filtro_linea.setter
    def filtro_linea(self, value: str):
        self.set("filtro_linea", value)

    @property
    def filtro_busqueda(self) -> str:
        return self._state.get("filtro_busqueda", "")

    @filtro_busqueda.setter
    def filtro_busqueda(self, value: str):
        self.set("filtro_busqueda", value)

    @property
    def filtro_tipo(self) -> str:
        return self._state.get("filtro_tipo", "")

    @filtro_tipo.setter
    def filtro_tipo(self, value: str):
        self.set("filtro_tipo", value)

    @property
    def pagina(self) -> int:
        return self._state.get("pagina", 0)

    @pagina.setter
    def pagina(self, value: int):
        self.set("pagina", value)

    @property
    def sort_column(self) -> str:
        return self._state.get("sort_column", "orden")

    @sort_column.setter
    def sort_column(self, value: str):
        self.set("sort_column", value)

    @property
    def sort_desc(self) -> bool:
        return self._state.get("sort_desc", False)

    @sort_desc.setter
    def sort_desc(self, value: bool):
        self.set("sort_desc", value)

    @property
    def is_loading(self) -> bool:
        return self._state.get("is_loading", False)

    @is_loading.setter
    def is_loading(self, value: bool):
        self.set("is_loading", value)

    @property
    def listas(self) -> dict:
        return self._state.get("listas", {})

    @listas.setter
    def listas(self, value: dict):
        self.set("listas", value)

    @property
    def lineas(self) -> list:
        return self._state.get("lineas", [])

    @lineas.setter
    def lineas(self, value: list):
        self.set("lineas", value)

    @property
    def selected_skus(self) -> set:
        return self._state.get("selected_skus", set())

    @selected_skus.setter
    def selected_skus(self, value: set):
        self.set("selected_skus", value)

    @property
    def status_message(self) -> str:
        return self._state.get("status_message", "")

    @status_message.setter
    def status_message(self, value: str):
        self.set("status_message", value)

    @property
    def status_level(self) -> str:
        return self._state.get("status_level", "muted")

    @status_level.setter
    def status_level(self, value: str):
        self.set("status_level", value)

    @property
    def current_view(self) -> int:
        return self._state.get("current_view", 0)

    @current_view.setter
    def current_view(self, value: int):
        self.set("current_view", value)

    def set_status(self, message: str, level: str = "muted"):
        self.status_message = message
        self.status_level = level

    @property
    def categorias_activas(self) -> set:
        return self._state.get("categorias_activas", set())

    @categorias_activas.setter
    def categorias_activas(self, value: set):
        self.set("categorias_activas", value)

    @property
    def traductor(self) -> dict:
        return self._state.get("traductor", {})

    @traductor.setter
    def traductor(self, value: dict):
        self.set("traductor", value)

    @property
    def inventario_search(self) -> str:
        return self._state.get("inventario_search", "")

    @inventario_search.setter
    def inventario_search(self, value: str):
        self.set("inventario_search", value)

    @property
    def traductor_file(self) -> str:
        return self._state.get("traductor_file", "")

    @traductor_file.setter
    def traductor_file(self, value: str):
        self.set("traductor_file", value)

    @property
    def dark_mode(self) -> bool:
        return self._state.get("dark_mode", True)

    @dark_mode.setter
    def dark_mode(self, value: bool):
        self.set("dark_mode", value)

    def reset(self):
        self._state.clear()
        self._notify("reset")
