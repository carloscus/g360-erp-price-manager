<!-- g360:agents:begin -->
# AGENTS.md — g360-erp-price-manager

Gestor de listas de precios con descuentos en cascada (CIPSA). App de escritorio

> El bloque entre los markers `g360:agents` lo genera `g360 agents` y se
> regenera sin perder lo que escribas afuera.

## Verificación

Un solo comando deja el repo listo y verifica que todo esté en verde:

```bash
uv sync
uv run pytest
```

- Stack: python (uv)
- Tests: pytest en `tests/`

## Instalación

```bash
uv sync
```


## Estructura

- `src/`
- `tests/`
- `g360_flet/`
- `main.py`

## Convenciones

- Tests con `pytest` en `tests/`.
- Dependencias con `uv` (`uv.lock` versionado).
- Comentarios que expliquen el *por qué*, no el *qué*.

## Reglas de este repo

- **Autosuficiente**: `git clone` + el comando de verificación debe dejar la app levantada y los tests en verde, sin red y sin ayuda de una persona.
- **Tests honestos**: nada de `it.skip`, `pytest.mark.skip`, `xfail` ni `assert true` para forzar verde.
- **Entorno declarativo**: toda variable de entorno va en `.env.example` con un default seguro.
- **Sin paths de tu máquina**: nada de rutas absolutas locales ni secretos en el código.
- **Evidencia**: al entregar, reportá el comando que corriste y su salida. Si no pudiste verificar, decilo.
<!-- g360:agents:end -->
