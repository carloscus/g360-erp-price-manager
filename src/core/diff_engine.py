"""Diff engine: compares price lists and computes field-level deltas."""

from __future__ import annotations

from typing import Any

from src.core.models import FieldDiff, Producto, ListaPrecio


def diff_producto(anterior: Producto, nuevo: Producto, tabla: str = "productos") -> list[FieldDiff]:
    diffs = []
    d_old = anterior.to_dict()
    d_new = nuevo.to_dict()

    for campo in d_old:
        if campo == "version":
            continue
        val_old = d_old[campo]
        val_new = d_new.get(campo)

        if _es_diferente(val_old, val_new):
            diffs.append(FieldDiff(
                sku=nuevo.sku,
                tabla=tabla,
                campo=campo,
                valor_anterior=val_old,
                valor_nuevo=val_new,
            ))

    return diffs


def diff_lista(anterior: ListaPrecio, nuevo: ListaPrecio) -> list[FieldDiff]:
    diffs = []

    if anterior.name != nuevo.name:
        diffs.append(FieldDiff(sku="", tabla="listas", campo="name", valor_anterior=anterior.name, valor_nuevo=nuevo.name))
    if anterior.base_discounts != nuevo.base_discounts:
        diffs.append(FieldDiff(sku="", tabla="listas", campo="base_discounts", valor_anterior=anterior.base_discounts, valor_nuevo=nuevo.base_discounts))

    sks_old = set(anterior.overrides.keys())
    sks_new = set(nuevo.overrides.keys())

    for sku in sks_new - sks_old:
        diffs.append(FieldDiff(sku=sku, tabla="overrides", campo="__nuevo__", valor_nuevo=nuevo.overrides[sku].to_dict()))

    for sku in sks_old - sks_new:
        diffs.append(FieldDiff(sku=sku, tabla="overrides", campo="__eliminado__", valor_anterior=anterior.overrides[sku].to_dict()))

    for sku in sks_old & sks_new:
        ov_old = anterior.overrides[sku]
        ov_new = nuevo.overrides[sku]
        if ov_old.discounts != ov_new.discounts:
            diffs.append(FieldDiff(sku=sku, tabla="overrides", campo="discounts", valor_anterior=ov_old.discounts, valor_nuevo=ov_new.discounts))
        if ov_old.fixed_price != ov_new.fixed_price:
            diffs.append(FieldDiff(sku=sku, tabla="overrides", campo="fixed_price", valor_anterior=ov_old.fixed_price, valor_nuevo=ov_new.fixed_price))

    return diffs


def diff_maestro_completo(
    maestro_anterior: dict[str, Producto],
    maestro_nuevo: dict[str, Producto],
) -> list[FieldDiff]:
    diffs = []
    skus_old = set(maestro_anterior.keys())
    skus_new = set(maestro_nuevo.keys())

    for sku in skus_new - skus_old:
        diffs.append(FieldDiff(sku=sku, tabla="productos", campo="__nuevo__", valor_nuevo=maestro_nuevo[sku].to_dict()))

    for sku in skus_old - skus_new:
        diffs.append(FieldDiff(sku=sku, tabla="productos", campo="__eliminado__", valor_anterior=maestro_anterior[sku].to_dict()))

    for sku in skus_old & skus_new:
        diffs.extend(diff_producto(maestro_anterior[sku], maestro_nuevo[sku]))

    return diffs


def _es_diferente(val_a: Any, val_b: Any) -> bool:
    if isinstance(val_a, list) and isinstance(val_b, list):
        return val_a != val_b
    if val_a is None and val_b is None:
        return False
    if val_a is None or val_b is None:
        return True
    if isinstance(val_a, float) and isinstance(val_b, (int, float)):
        return abs(val_a - float(val_b)) > 0.0001
    return val_a != val_b
