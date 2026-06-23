"""Supabase client for remote sync of price lists and catalogs."""

from __future__ import annotations

from typing import Optional

from src.core.models import Producto, ListaPrecio, FieldDiff


from src.core.constants import SUPABASE_URL, SUPABASE_KEY


class SupabaseClient:
    """Remote sync client for pushing/ pulling price lists and catalogs from Supabase."""

    def __init__(self, url: str = "", api_key: str = ""):
        self._url = url or SUPABASE_URL
        self._api_key = api_key or SUPABASE_KEY
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and bool(self._url) and bool(self._api_key)

    def conectar(self, url: str, api_key: str) -> bool:
        self._url = url
        self._api_key = api_key
        self._connected = False
        try:
            import requests
            resp = requests.get(
                f"{self._url}/rest/v1/productos?select=sku&limit=1",
                headers={
                    "apikey": self._api_key,
                    "Authorization": f"Bearer {self._api_key}",
                },
                timeout=10,
            )
            self._connected = resp.status_code == 200
        except Exception:
            self._connected = False
        return self._connected

    def subir_productos(self, productos: list[Producto]) -> dict:
        if not self.is_connected:
            return {"status": "error", "message": "No conectado a Supabase"}
        return {"status": "skip", "message": "Supabase sync pendiente (fase 10)"}

    def subir_lista(self, lista: ListaPrecio) -> dict:
        if not self.is_connected:
            return {"status": "error", "message": "No conectado a Supabase"}
        return {"status": "skip", "message": "Supabase sync pendiente (fase 10)"}

    def subir_diffs(self, diffs: list[FieldDiff]) -> dict:
        if not self.is_connected:
            return {"status": "error", "message": "No conectado a Supabase"}
        return {"status": "skip", "message": "Supabase sync pendiente (fase 10)"}

    def descargar_productos(self) -> list[Producto]:
        if not self.is_connected:
            return []
        return []

    def descargar_listas(self) -> list[ListaPrecio]:
        if not self.is_connected:
            return []
        return []

    def get_stats(self) -> dict:
        return {
            "connected": self.is_connected,
            "url": self._url[:30] + "..." if self._url else "",
            "phase": "10 (pendiente)",
        }
