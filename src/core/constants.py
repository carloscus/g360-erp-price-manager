"""Paths, file names, and environment keys used across the application."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
DATA_DIR = ASSETS_DIR / "data"
SAMPLES_DIR = BASE_DIR / "samples"
MAESTRO_FILE = DATA_DIR / "catalogo_maestro.json"
MAESTRO_COMERCIAL_FILE = DATA_DIR / "maestro_comercial.json"
LISTAS_FILE = DATA_DIR / "listas_precios.json"
PRICING_RULES_FILE = DATA_DIR / "pricing_rules.json"
SNAPSHOT_DIR = BASE_DIR / ".snapshots"

S1_URL = os.getenv(
    "S1_URL",
    "http://appweb.cipsa.com.pe:8054/AlmacenStock/DownLoadFiles"
    "?value=%7B%22parametroX1%22%3A%220%22%2C%22parametroX2%22%3A%220%22%7D"
)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

IGV_RATE = 0.18

WINDOW_WIDTH = 1350
WINDOW_HEIGHT = 780
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 600

APP_NAME = "G360 ERP Price List"
APP_TITLE = "G360 ERP Price List - CIPSA"
APP_VERSION = "1.1.0"
