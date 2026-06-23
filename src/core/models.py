"""Domain models: Producto, PricingRules, ListaPrecio, SkuPendiente."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PriceType(str, Enum):
    """Product pricing mode: NORMAL (discount chain) or FIJO (fixed price override)."""
    NORMAL = "NORMAL"
    FIJO = "FIJO"


FIXED_REASONS = ["LIQUIDACION", "PROMOCION", "NEGOCIADO", "REMAJE", "OFERTA"]


class ActiveState(str, Enum):
    """Active status after cross-referencing ERP data with stock (ACT/PEND/INACT)."""
    ACT = "ACT"
    PEND = "PEND"
    INACT = "INACT"


class StockStatus(str, Enum):
    """Stock availability level: OK (available), BJ (low), AGOTADO (out of stock)."""
    OK = "OK"
    BJ = "BJ"
    AGOTADO = "AGOTADO"


@dataclass
class Producto:
    """Single product with all pricing, discount, stock, and metadata fields."""
    sku: str
    sequence: int = 0
    description: str = ""
    full_name: str = ""
    line: str = ""
    category: str = ""
    family: str = ""
    group: str = ""
    units_per_box: int = 1

    def __post_init__(self):
        if self.units_per_box < 1:
            object.__setattr__(self, 'units_per_box', 1)
    list_price: float = 0.0
    discount_chain: list[float] = field(default_factory=list)
    special_discount_adjust: float = 0.0
    price_type: str = PriceType.NORMAL.value
    fixed_price: float | None = None
    fixed_reason: str = ""
    net_price: float = 0.0
    price_with_tax: float = 0.0
    stock: int = 0
    stock_status: str = StockStatus.OK.value
    active: str = ActiveState.ACT.value
    sort_key: str = ""
    ean13: str = ""
    weight_kg: float = 0.0
    customer_sku: str = ""
    currency: str = "PEN"
    keywords: list[str] = field(default_factory=list)
    unit_of_measure: str = "UND"
    image_url: str = ""
    subcategory: str = ""
    product_type: str = ""
    version: int = 1
    notes: str = ""
    special_discount: float = 0.0
    special_label: str = ""
    pre_dispatch: int = 0
    warehouse_stock: dict[str, int] = field(default_factory=dict)
    commercial_discounts: list[float] = field(default_factory=list)
    rebate_override: float = 0.0
    additional_discounts: list[float] = field(default_factory=list)
    special_override: float = 0.0
    special_label_override: str = ""
    catalog_price: float = 0.0
    precio_divergente: bool = False
    feria_discount: float = 0.0
    evento_discount: float = 0.0
    _dc_ref: Optional[DescuentosCategoria] = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "sequence": self.sequence,
            "description": self.description,
            "full_name": self.full_name,
            "line": self.line,
            "category": self.category,
            "family": self.family,
            "group": self.group,
            "units_per_box": self.units_per_box,
            "list_price": self.list_price,
            "discount_chain": self.discount_chain,
            "price_type": self.price_type,
            "fixed_price": self.fixed_price,
            "fixed_reason": self.fixed_reason,
            "net_price": self.net_price,
            "price_with_tax": self.price_with_tax,
            "stock": self.stock,
            "stock_status": self.stock_status,
            "active": self.active,
            "sort_key": self.sort_key,
            "ean13": self.ean13,
            "weight_kg": self.weight_kg,
            "customer_sku": self.customer_sku,
            "currency": self.currency,
            "keywords": self.keywords,
            "unit_of_measure": self.unit_of_measure,
            "image_url": self.image_url,
            "subcategory": self.subcategory,
            "product_type": self.product_type,
            "version": self.version,
            "notes": self.notes,
            "special_discount": self.special_discount,
            "special_label": self.special_label,
            "pre_dispatch": self.pre_dispatch,
            "warehouse_stock": self.warehouse_stock,
            "commercial_discounts": self.commercial_discounts,
            "rebate_override": self.rebate_override,
            "additional_discounts": self.additional_discounts,
            "special_override": self.special_override,
            "special_label_override": self.special_label_override,
            "special_discount_adjust": self.special_discount_adjust,
            "feria_discount": self.feria_discount,
            "evento_discount": self.evento_discount,
        "catalog_price": self.catalog_price,
        "precio_divergente": self.precio_divergente,
        "_dc_ref_category": self._dc_ref.category if self._dc_ref else None,
    }

    @classmethod
    def from_dict(cls, d: dict) -> Producto:
        obj = cls(
            sku=str(d.get("sku", "")),
            sequence=int(d.get("sequence", d.get("orden", 0))),
            description=str(d.get("description", d.get("descripcion", d.get("nombre", d.get("nombre_corto", ""))))),
            full_name=str(d.get("full_name", d.get("nombre_completo", d.get("description", d.get("descripcion", d.get("nombre", "")))))),
            line=str(d.get("line", d.get("linea", ""))),
            category=str(d.get("category", d.get("categoria", ""))),
            family=str(d.get("family", d.get("familia", ""))),
            group=str(d.get("group", d.get("grupo", ""))),
            units_per_box=int(d.get("units_per_box", d.get("un_bx", 1))) if d.get("units_per_box", d.get("un_bx")) not in (None, "") else 1,
            list_price=float(d.get("list_price", d.get("precio_lista", 0))) if d.get("list_price", d.get("precio_lista")) not in (None, "") else 0.0,
            discount_chain=d.get("discount_chain", d.get("cadena_descuentos", d.get("descuentos", []))),
            price_type=str(d.get("price_type", d.get("tipo_precio", "NORMAL"))),
            fixed_price=float(d.get("fixed_price", d.get("precio_fijo"))) if d.get("fixed_price", d.get("precio_fijo")) not in (None, "") else None,
            fixed_reason=str(d.get("fixed_reason", d.get("motivo_fijo", ""))),
            net_price=float(d.get("net_price", d.get("precio_neto", d.get("precio_final", 0)))),
            price_with_tax=float(d.get("price_with_tax", d.get("precio_cigv", 0))),
            stock=int(d.get("stock", 0)),
            stock_status=str(d.get("stock_status", "OK")),
            active=str(d.get("active", d.get("activo", "ACT"))),
            sort_key=str(d.get("sort_key", d.get("sort", ""))),
            ean13=str(d.get("ean13", "")),
            weight_kg=float(d.get("weight_kg", d.get("peso_kg", 0))) if d.get("weight_kg", d.get("peso_kg")) not in (None, "") else 0.0,
            customer_sku=str(d.get("customer_sku", d.get("sku_cliente", ""))),
            currency=str(d.get("currency", d.get("moneda", "PEN"))),
            keywords=d.get("keywords", []),
            unit_of_measure=str(d.get("unit_of_measure", d.get("unidad_medida", "UND"))),
            image_url=str(d.get("image_url", d.get("imagen_url", ""))),
            subcategory=str(d.get("subcategory", d.get("subcategoria", ""))),
            product_type=str(d.get("product_type", d.get("tipo", ""))),
            version=int(d.get("version", 1)),
            notes=str(d.get("notes", d.get("observacion", ""))),
            special_discount=float(d.get("special_discount", d.get("descuento_especial", 0))) if d.get("special_discount", d.get("descuento_especial")) not in (None, "") else 0.0,
            special_label=str(d.get("special_label", d.get("especial_label", ""))),
            pre_dispatch=int(d.get("pre_dispatch", d.get("predespacho", 0))),
            warehouse_stock=d.get("warehouse_stock", d.get("stock_almacenes", {})),
            commercial_discounts=d.get("commercial_discounts", d.get("comerciales", d.get("descuentos_override", []))),
            rebate_override=float(d.get("rebate_override", 0)) if d.get("rebate_override") not in (None, "") else 0.0,
            additional_discounts=d.get("additional_discounts", d.get("adicionales", d.get("adic_fijos", d.get("adic_fijos_override", [])))),
            special_discount_adjust=float(d.get("special_discount_adjust", 0)) if d.get("special_discount_adjust") not in (None, "") else 0.0,
            special_override=float(d.get("special_override", d.get("especial_override", 0))) if d.get("special_override", d.get("especial_override")) not in (None, "") else 0.0,
            special_label_override=str(d.get("special_label_override", d.get("especial_label_override", ""))),
            feria_discount=float(d.get("feria_discount", 0)) if d.get("feria_discount") not in (None, "") else 0.0,
            evento_discount=float(d.get("evento_discount", 0)) if d.get("evento_discount") not in (None, "") else 0.0,
            catalog_price=float(d.get("catalog_price", 0)) if d.get("catalog_price") not in (None, "") else 0.0,
            precio_divergente=bool(d.get("precio_divergente", False)),
        )
        dc_cat = d.get("_dc_ref_category")
        if dc_cat:
            obj._dc_ref_category = dc_cat
        return obj

    def is_fixed_price(self) -> bool:
        return self.price_type == PriceType.FIJO.value and bool(self.fixed_price and self.fixed_price > 0)

    def has_overrides(self) -> bool:
        return bool(
            self.commercial_discounts
            or self.rebate_override > 0
            or self.additional_discounts
            or self.special_override > 0
            or self.special_discount_adjust > 0
            or self.feria_discount > 0
            or self.evento_discount > 0
        )

    def clear_overrides(self):
        self.commercial_discounts = []
        self.rebate_override = 0.0
        self.additional_discounts = []
        self.special_override = 0.0
        self.special_label_override = ""
        self.special_discount_adjust = 0.0
        self.feria_discount = 0.0
        self.evento_discount = 0.0


@dataclass
class PricingRules:
    """P2 dataset: reglas de pricing independientes del catálogo."""
    categories: dict[str, str] = field(default_factory=dict)
    discounts: dict[str, list[float]] = field(default_factory=dict)
    additional_discounts: dict[str, list[float]] = field(default_factory=dict)
    rebate_overrides: dict[str, float] = field(default_factory=dict)
    special_overrides: dict[str, float] = field(default_factory=dict)
    special_labels: dict[str, str] = field(default_factory=dict)
    fixed_prices: dict[str, tuple[float, str]] = field(default_factory=dict)
    special_adjust: dict[str, float] = field(default_factory=dict)
    feria_discounts: dict[str, float] = field(default_factory=dict)
    evento_discounts: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    translator: dict[str, str] = field(default_factory=dict)
    units_per_box: dict[str, int] = field(default_factory=dict)
    currency: dict[str, str] = field(default_factory=dict)
    sequence: dict[str, int] = field(default_factory=dict)

    def apply_to(self, p: Producto):
        sku = p.sku
        if sku in self.categories:
            p.category = self.categories[sku]
        if sku in self.units_per_box:
            p.units_per_box = self.units_per_box[sku]
        if sku in self.currency:
            p.currency = self.currency[sku]
        if sku in self.sequence:
            p.sequence = self.sequence[sku]
        if sku in self.discounts:
            p.commercial_discounts = list(self.discounts[sku])
        if sku in self.additional_discounts:
            p.additional_discounts = list(self.additional_discounts[sku])
        if sku in self.rebate_overrides:
            p.rebate_override = self.rebate_overrides[sku]
        if sku in self.special_overrides:
            p.special_override = self.special_overrides[sku]
        if sku in self.special_labels:
            p.special_label_override = self.special_labels[sku]
        if sku in self.fixed_prices:
            price, reason = self.fixed_prices[sku]
            if price > 0:
                p.price_type = "FIJO"
                p.fixed_price = price
                p.fixed_reason = reason or ""
        if sku in self.special_adjust:
            p.special_discount_adjust = self.special_adjust[sku]
        if sku in self.feria_discounts:
            p.feria_discount = self.feria_discounts[sku]
        if sku in self.evento_discounts:
            p.evento_discount = self.evento_discounts[sku]
        if sku in self.notes:
            p.notes = self.notes[sku]
        if sku in self.translator:
            p.customer_sku = self.translator[sku]

    def has_data_for(self, sku: str) -> bool:
        return any((
            sku in self.categories,
            sku in self.discounts,
            sku in self.fixed_prices,
        ))

    def to_dict(self) -> dict:
        return {
            "categories": dict(self.categories),
            "discounts": {k: list(v) for k, v in self.discounts.items()},
            "additional_discounts": {k: list(v) for k, v in self.additional_discounts.items()},
            "rebate_overrides": dict(self.rebate_overrides),
            "special_overrides": dict(self.special_overrides),
            "special_labels": dict(self.special_labels),
            "fixed_prices": {k: list(v) for k, v in self.fixed_prices.items()},
            "special_adjust": {k: float(v) for k, v in self.special_adjust.items()},
            "feria_discounts": dict(self.feria_discounts),
            "evento_discounts": dict(self.evento_discounts),
            "notes": dict(self.notes),
            "translator": dict(self.translator),
            "units_per_box": {k: int(v) for k, v in self.units_per_box.items()},
            "currency": dict(self.currency),
            "sequence": dict(self.sequence),
        }

    @classmethod
    def from_dict(cls, d: dict) -> PricingRules:
        fixed = {}
        for k, v in d.get("fixed_prices", {}).items():
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                fixed[k] = (float(v[0]), str(v[1]))
            else:
                fixed[k] = (float(v) if v else 0.0, "")
        return cls(
            categories=dict(d.get("categories", {})),
            discounts={k: list(v) for k, v in d.get("discounts", {}).items()},
            additional_discounts={k: list(v) for k, v in d.get("additional_discounts", {}).items()},
            rebate_overrides={k: float(v) for k, v in d.get("rebate_overrides", {}).items()},
            special_overrides={k: float(v) for k, v in d.get("special_overrides", {}).items()},
            special_labels=dict(d.get("special_labels", {})),
            fixed_prices=fixed,
            special_adjust={k: float(v) for k, v in d.get("special_adjust", {}).items()},
            feria_discounts={k: float(v) for k, v in d.get("feria_discounts", {}).items()},
            evento_discounts={k: float(v) for k, v in d.get("evento_discounts", {}).items()},
            notes=dict(d.get("notes", {})),
            translator=dict(d.get("translator", {})),
            units_per_box={k: int(v) for k, v in d.get("units_per_box", {}).items()},
            currency=dict(d.get("currency", {})),
            sequence={k: int(v) for k, v in d.get("sequence", {}).items()},
        )


@dataclass
class Override:
    """Per-SKU override of discount chain and/or fixed price."""
    sku: str
    discounts: list[float] | None = None
    fixed_price: float | None = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"sku": self.sku}
        if self.discounts is not None:
            d["discounts"] = self.discounts
        if self.fixed_price is not None:
            d["fixed_price"] = self.fixed_price
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Override:
        return cls(
            sku=str(d.get("sku", "")),
            discounts=d.get("discounts", d.get("descuentos")),
            fixed_price=float(d.get("fixed_price", d.get("precio_fijo"))) if d.get("fixed_price", d.get("precio_fijo")) not in (None, "") else None,
        )


@dataclass
class DescuentosCategoria:
    """Discount chain applied to all products in a given category."""
    category: str
    discounts: list[float] = field(default_factory=list)
    fixed_discounts: list[float] = field(default_factory=list)
    rebate: float = 0.0
    special_discount: float = 0.0
    special_label: str = ""

    @property
    def full_discounts(self) -> list[float]:
        return self.discounts + self.fixed_discounts

    @property
    def group1(self) -> list[float]:
        return self.discounts + ([self.rebate] if self.rebate > 0 else [])

    @property
    def group2(self) -> list[float]:
        return self.fixed_discounts + ([self.special_discount] if self.special_discount > 0 else [])

    @property
    def sum_desc01(self) -> float:
        if not self.group1:
            return 0.0
        factor = 1.0
        for d in self.group1:
            if d > 0:
                factor *= (1 - d)
        return round(1 - factor, 6)

    @property
    def sum_desc02(self) -> float:
        if not self.group2:
            return 0.0
        factor = 1.0
        for d in self.group2:
            if d > 0:
                factor *= (1 - d)
        return round(1 - factor, 6)

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "discounts": self.discounts,
            "fixed_discounts": self.fixed_discounts,
            "rebate": self.rebate,
            "special_discount": self.special_discount,
            "special_label": self.special_label,
        }

    @classmethod
    def from_dict(cls, d: dict) -> DescuentosCategoria:
        return cls(
            category=str(d.get("category", d.get("categoria", ""))),
            discounts=d.get("discounts", d.get("descuentos", [])),
            fixed_discounts=d.get("fixed_discounts", d.get("descuentos_fijos", [])),
            rebate=float(d.get("rebate", 0)) if d.get("rebate") not in (None, "") else 0.0,
            special_discount=float(d.get("special_discount", d.get("descuento_especial", 0))) if d.get("special_discount", d.get("descuento_especial")) not in (None, "") else 0.0,
            special_label=str(d.get("special_label", d.get("especial_label", ""))),
        )

    def display(self) -> str:
        all_desc = self.full_discounts
        parts = [str(int(d * 100)) for d in all_desc]
        if self.rebate > 0:
            parts.append(f"R{int(self.rebate * 100)}")
        if self.special_discount > 0:
            label = self.special_label or "Esp"
            parts.append(f"{label}{int(self.special_discount * 100)}")
        return "-".join(parts) if parts else "—"

    def display_commercial(self) -> str:
        parts = [str(int(d * 100)) for d in self.discounts]
        if self.rebate > 0:
            parts.append(f"R{int(self.rebate * 100)}")
        return "-".join(parts) if parts else "—"

    def display_fixed(self) -> str:
        parts = [str(int(d * 100)) for d in self.fixed_discounts]
        if self.special_discount > 0:
            label = self.special_label or "Esp"
            parts.append(f"{label}{int(self.special_discount * 100)}")
        return "-".join(parts) if parts else "—"


@dataclass
class ListaPrecio:
    """Named discount list: category discounts, per-SKU overrides, base discount chain."""
    id: str
    name: str = ""
    base: str | None = None
    base_discounts: list[float] = field(default_factory=list)
    discounts_by_category: dict[str, DescuentosCategoria] = field(default_factory=dict)
    overrides: dict[str, Override] = field(default_factory=dict)
    active: bool = True
    version: int = 1

    def get_discounts_for_category(self, category: str) -> list[float]:
        if category in self.discounts_by_category:
            return self.discounts_by_category[category].full_discounts
        return self.base_discounts

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "base": self.base,
            "base_discounts": self.base_discounts,
            "discounts_by_category": {k: v.to_dict() for k, v in self.discounts_by_category.items()},
            "overrides": {k: v.to_dict() for k, v in self.overrides.items()},
            "active": self.active,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ListaPrecio:
        overrides = {}
        for k, v in d.get("overrides", {}).items():
            overrides[k] = Override.from_dict(v) if isinstance(v, dict) else v
        desc_cat = {}
        for k, v in d.get("discounts_by_category", d.get("descuentos_por_categoria", {})).items():
            desc_cat[k] = DescuentosCategoria.from_dict(v) if isinstance(v, dict) else v
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", d.get("nombre", ""))),
            base=d.get("base"),
            base_discounts=d.get("base_discounts", d.get("descuentos_base", [])),
            discounts_by_category=desc_cat,
            overrides=overrides,
            active=bool(d.get("active", d.get("activa", True))),
            version=int(d.get("version", 1)),
        )


@dataclass
class SkuPendiente:
    """SKU that could not be parsed from a source file, logged for review."""
    sku: str
    description: str = ""
    origin: str = ""
    detection_date: str = ""
    stock: int = 0

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "description": self.description,
            "origin": self.origin,
            "detection_date": self.detection_date,
            "stock": self.stock,
        }


@dataclass
class ParsedSource:
    """Result of parsing a single data source: products, column mapping, errors."""
    filename: str
    sheet_name: str = ""
    total_rows: int = 0
    columns_detected: dict[str, int] = field(default_factory=dict)
    columns_unmapped: list[str] = field(default_factory=list)
    productos: list[Producto] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        n_map = len(self.columns_detected)
        n_unmap = len(self.columns_unmapped)
        return f"{self.filename}: {self.total_rows} rows, {n_map} cols recognized, {n_unmap} ignored"


@dataclass
class MergeResult:
    """Result of merging parsed products into the master catalog."""
    productos: list[Producto] = field(default_factory=list)
    sku_pendientes: list[SkuPendiente] = field(default_factory=list)
    conflictos: list[str] = field(default_factory=list)
    fuentes_usadas: int = 0


@dataclass
class FieldDiff:
    """A single field-level difference between two price lists or versions."""
    sku: str
    tabla: str
    campo: str
    valor_anterior: Any = None
    valor_nuevo: Any = None

    @property
    def es_nuevo(self) -> bool:
        return self.campo == "__nuevo__"

    @property
    def es_eliminado(self) -> bool:
        return self.campo == "__eliminado__"


from src.core.config_manager import config_manager


def get_grupo_map() -> dict[str, str]:
    return config_manager.grupo_map


def get_default_discounts() -> dict[str, list[float]]:
    return config_manager.default_discounts


def get_preset_descuentos() -> dict[str, list[dict]]:
    return config_manager.preset_descuentos


def get_descuentos_base(category: str) -> list[float]:
    return config_manager.default_discounts.get(category, [])


def crear_listas_simuladas() -> dict[str, ListaPrecio]:
    listas = {}
    presets = config_manager.preset_descuentos
    
    # Intentamos armar listas basadas en los presets si están disponibles
    # o caemos en el hardcodeado previo como fallback
    
    def _get_preset(cat, label):
        for p in presets.get(cat, []):
            if p["label"] == label:
                return DescuentosCategoria(cat, p["discounts"], p["fixed"], p["rebate"])
        return None

    # Lista Estandar
    lista1 = ListaPrecio(
        id="estandar", name="Estandar",
        discounts_by_category={
            "VINIFAN": _get_preset("VINIFAN", "25-4") or DescuentosCategoria("VINIFAN", [0.25, 0.04]),
            "REPRESENTADAS": _get_preset("REPRESENTADAS", "25-4") or DescuentosCategoria("REPRESENTADAS", [0.25, 0.04]),
            "VINIBALL": _get_preset("VINIBALL", "15-10-3") or DescuentosCategoria("VINIBALL", [0.15, 0.10], [0.03]),
        },
    )
    listas[lista1.id] = lista1

    # Lista Premium
    lista2 = ListaPrecio(
        id="premium", name="Premium",
        discounts_by_category={
            "VINIFAN": _get_preset("VINIFAN", "25-5") or DescuentosCategoria("VINIFAN", [0.25, 0.05]),
            "REPRESENTADAS": _get_preset("REPRESENTADAS", "25-5") or DescuentosCategoria("REPRESENTADAS", [0.25, 0.05]),
            "VINIBALL": _get_preset("VINIBALL", "15-10-5") or DescuentosCategoria("VINIBALL", [0.15, 0.10], [0.05]),
        },
    )
    listas[lista2.id] = lista2

    return listas
