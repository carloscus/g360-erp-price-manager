# G360 ERP Price Manager

Gestor de listas de precios con descuentos en cascada (CIPSA). App de escritorio
(Flet) que ingiere excels del ERP, normaliza las columnas, calcula precios y
descuentos por categoría, y exporta el resultado.

> Microherramienta del ecosistema **G360** para apoyo CRM y gestión de datos.

## Qué hace

1. **Ingesta**: lee excels/XLSX/XLS del ERP (`samples/` tiene ejemplos).
2. **Normalización**: detecta columnas por alias (`FIELD_KEYWORDS` en
   `assets/data/config.json`), sin hardcodear índices.
3. **Cálculo**: motor de precios con `Decimal` y descuentos en cascada por
   categoría (`src/core/engine/`).
4. **Exportación**: genera el resultado en XLSX/JSON (`src/export/`).
5. **UI**: app Flet con vistas de precios, descuentos, inventario y
   configuración (`src/ui/`).

## Requisitos

- **Python 3.11+** (lo instala `uv` automáticamente)
- **[uv](https://docs.astral.sh/uv/)** — gestor de entorno y dependencias
- Red **solo** para la instalación inicial de dependencias

## Verificación

Un solo comando deja el repo listo y verifica que todo esté en verde:

```bash
uv sync
uv run pytest
```

## Ejecutar la app

```bash
# Windows: instala uv + Python + dependencias y crea el acceso directo
run.bat

# o manual
uv sync
uv run python main.py
```

## Configuración

Copia `.env.example` a `.env` y ajustá los valores:

| Variable | Para qué |
|----------|----------|
| `S1_URL` | Descarga de stock desde el ERP CIPSA |
| `SUPABASE_URL` | Búsqueda de clientes (opcional) |
| `SUPABASE_KEY` | Clave de Supabase (opcional) |

Sin configuración, la app arranca igual: la búsqueda de clientes degrada a
captura manual.

## Estructura

```text
main.py                 # punto de entrada Flet
assets/data/config.json # reglas de negocio: alias de columnas, descuentos, categorías
samples/                # excels de ejemplo
src/core/               # motor: parsers, modelos, config, cálculo de precios
src/ui/                 # vistas y componentes Flet
src/export/             # generación de XLSX/JSON
tests/                  # tests con pytest
```

## Estándares

El proyecto sigue el modelo de estandarización de 3 capas (fuente flexible →
núcleo estándar → UI reconocible). Ver [`DEVELOPER.md`](DEVELOPER.md).

## Ecosistema G360

- **[g360-cli](https://github.com/carloscus/g360-cli)** — CLI de bootstrap del ecosistema
- **[g360-master-data](https://github.com/carloscus/g360-master-data)** — catálogo maestro
- **[g360-signature](https://github.com/carloscus/g360-signature)** — branding

---

**Marca**: G360 · Microherramientas para apoyo CRM y datos en CIPSA
**Powered by** [g360-signature](https://github.com/carloscus/g360-signature)
