# Samples - Archivos de Ejemplo

Coloca aquí archivos XLSX/XLS/JSON de ejemplo para probar el parser inteligente.

## Formatos soportados

- **plantilla_precios.xlsx**: 3 hojas (PRODUCTOS, DESCUENTOS, PRECIOS_FIJOS)
- **catalogo_productos.json**: JSON con metadata + productos
- **stock_erp.xls**: Excel del ERP con ~14000 SKUs (se depura por capas)
- **lista_precios.xlsx**: Excel con lista de precios de un cliente/canal

## Formato JSON esperado

```json
{
  "metadata": {
    "version": "2.0.0",
    "total_productos": 1088
  },
  "productos": [
    {
      "sku": "AB001",
      "nombre": "Producto ejemplo",
      "linea": "VINIBALL",
      "precio_lista": 100.00,
      "cadena_descuentos": [0.25, 0.04, 0.02],
      "tipo_precio": "NORMAL",
      "precio_fijo": null,
      "motivo_fijo": "",
      "un_bx": 12
    }
  ]
}
```

## Columnas detectadas automáticamente

El smart parser detecta por keywords:
- SKU: CÓDIGO, SKU, COD.
- Precio: P. LISTA, PRECIO, P.L
- Descuentos: D1..D7, DESC1..DESC7, DSCTO1..DSCTO7
- Precio Fijo: P. FIJO, PRECIO FIJO, P.ESP
- Stock: STOCK, SALDO, CANTIDAD
