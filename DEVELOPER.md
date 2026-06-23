# Guía de Estándares de Ingeniería - G360 Ecosystem

Este proyecto sigue el modelo de estandarización de 3 capas para garantizar la flexibilidad ante cambios en las fuentes de datos (ERP) y la consistencia en el código y la interfaz.

## 1. Modelo de Estandarización de 3 Capas

### Capa 1: Fuente de Datos (Input Flexible)
- **Origen:** Excels del ERP, archivos JSON externos, APIs de terceros.
- **Nomenclatura:** Variable (Español/Inglés, Abreviaturas, Mayúsculas).
- **Manejo:** Se utilizan diccionarios de sinónimos en `assets/data/config.json` bajo la llave `FIELD_KEYWORDS`.
- **Regla:** Nunca hardcodear índices de columnas (ej. `row[5]`). Usar siempre `detectar_columnas(headers)`.

### Capa 2: Núcleo de la Aplicación (Código Estándar)
- **Ubicación:** `src/core/models.py`, `src/core/engine/`.
- **Nomenclatura:** **Inglés Estándar** en `snake_case`.
- **Tipos de Datos:** 
    - Precios y porcentajes: `decimal.Decimal` para precisión financiera.
    - Identificadores: `sku` (string normalizado).
- **Regla:** El código interno no debe conocer los nombres de las columnas del Excel original.

### Capa 3: Interfaz de Usuario (UI Reconocible)
- **Ubicación:** `src/ui/views/`, `src/ui/components/`.
- **Nomenclatura:** **Español Amigable** y términos de negocio.
- **Visualización:** 
    - Formatos de moneda: `S/ 1,234.56`.
    - Etiquetas: "Artículo", "P. Lista", "U/Caja".
- **Regla:** Las etiquetas de la UI son independientes de los nombres de los atributos en el código.

---

## 2. Flujo de Datos y Normalización

1. **Ingesta:** El `SourceManager` recibe un archivo.
2. **Detección:** Los parsers (`smart_parser`, `plantilla_parser`) identifican las columnas usando `FIELD_KEYWORDS`.
3. **Conversión:** Los datos se transforman a objetos `Producto` usando `Producto.from_dict()`.
4. **Cálculo:** El `price_engine` realiza cálculos usando `Decimal`.
5. **Estado:** El `AppState` centraliza la información para la UI.

## 3. Configuración Centralizada (`config.json`)

Cualquier cambio en la lógica de negocio (nuevas categorías, cambios en alias de columnas, descuentos por defecto) debe realizarse en `assets/data/config.json` para evitar la necesidad de recompilar o modificar el código fuente.
