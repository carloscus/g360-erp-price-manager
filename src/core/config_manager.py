"""Central configuration: default discounts, primary categories, P2 overrides."""

import json
from pathlib import Path
from typing import Any

from src.core.constants import DATA_DIR


class ConfigManager:
    """Singleton config: default discounts, primary categories, P2 overrides loaded from JSON."""

    _instance = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self._config = {
            "PRIMARY_CATEGORIES": ["VINIFAN", "VINIBALL", "REPRESENTADAS"],
            "GRUPO_MAP": {},
            "DEFAULT_DISCOUNTS_BY_CATEGORY": {},
            "PRESET_DESCUENTOS": {},
        }

        config_path = DATA_DIR / "config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config.update(json.load(f))
            except Exception:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    @property
    def primary_categories(self) -> list[str]:
        return self.get("PRIMARY_CATEGORIES", [])

    @property
    def grupo_map(self) -> dict[str, str]:
        return self.get("GRUPO_MAP", {})

    @property
    def default_discounts(self) -> dict[str, list[float]]:
        return self.get("DEFAULT_DISCOUNTS_BY_CATEGORY", {})

    @property
    def preset_descuentos(self) -> dict[str, list[dict]]:
        return self.get("PRESET_DESCUENTOS", {})

    @property
    def field_keywords(self) -> dict[str, list[str]]:
        # Los alias de columnas viven en assets/data/config.json (capa 1 del
        # modelo de estandarización). No se hardcodean en el código.
        return self.get("FIELD_KEYWORDS", {})


# Instancia única (Singleton)
config_manager = ConfigManager()
