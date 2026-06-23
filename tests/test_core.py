import pytest
from src.core.models import Producto, ListaPrecio, Override, PriceType, FIXED_REASONS
from src.core.engine.price_engine import (
    calcular_precio_neto, calcular_precio_cigv, calcular_cascada, evaluar_producto,
)
from src.core.engine.sku_matcher import (
    cruzar_stock_con_maestro, filtrar_con_stock, filtrar_con_precio,
    depurar_por_capas, segmentar_por_linea,
)
from src.core.diff_engine import diff_producto, diff_maestro_completo, _es_diferente
from src.core.models import FieldDiff


class TestModels:
    def test_producto_defaults(self):
        p = Producto(sku="TEST01")
        assert p.price_type == "NORMAL"
        assert p.fixed_price is None
        assert p.fixed_reason == ""
        assert p.discount_chain == []
        assert p.active == "ACT"

    def test_producto_to_dict_roundtrip(self):
        p = Producto(sku="AB001", description="Test", list_price=100.0, discount_chain=[0.25, 0.04])
        d = p.to_dict()
        p2 = Producto.from_dict(d)
        assert p2.sku == p.sku
        assert p2.description == p.description
        assert p2.discount_chain == p.discount_chain

    def test_price_type_solo_dos(self):
        assert len(PriceType) == 2
        assert PriceType.NORMAL.value == "NORMAL"
        assert PriceType.FIJO.value == "FIJO"

    def test_motivos_fijo(self):
        assert "LIQUIDACION" in FIXED_REASONS
        assert "NEGOCIADO" in FIXED_REASONS
        assert "REMAJE" in FIXED_REASONS

    def test_override_to_dict(self):
        ov = Override(sku="X1", discounts=[0.25], fixed_price=50.0)
        d = ov.to_dict()
        assert d["discounts"] == [0.25]
        assert d["fixed_price"] == 50.0

    def test_lista_from_dict(self):
        data = {
            "id": "lista1",
            "name": "Distribuidor",
            "base_discounts": [0.25, 0.04],
            "overrides": {"X1": {"sku": "X1", "fixed_price": 50.0}},
        }
        lp = ListaPrecio.from_dict(data)
        assert lp.name == "Distribuidor"
        assert "X1" in lp.overrides
        assert lp.overrides["X1"].fixed_price == 50.0


class TestPriceEngine:
    def test_cascada_simple(self):
        neto = calcular_precio_neto(100.0, [0.25, 0.04, 0.02])
        factor = 0.75 * 0.96 * 0.98
        expected = round(100.0 * factor, 2)
        assert abs(neto - expected) < 0.01

    def test_cascada_vacio(self):
        assert calcular_precio_neto(100.0, []) == 100.0

    def test_igv(self):
        cigv = calcular_precio_cigv(100.0)
        assert abs(cigv - 118.0) < 0.01

    def test_evaluar_producto_normal(self):
        p = Producto(sku="T1", list_price=100.0, discount_chain=[0.25])
        p = evaluar_producto(p)
        assert p.price_type == "NORMAL"
        assert p.net_price == 75.0
        assert abs(p.price_with_tax - 88.5) < 0.01

    def test_evaluar_producto_fijo(self):
        p = Producto(sku="T2", price_type="FIJO", fixed_price=50.0, list_price=100.0, discount_chain=[0.25])
        p = evaluar_producto(p)
        assert p.price_type == "FIJO"
        assert p.net_price == 50.0
        assert abs(p.price_with_tax - 59.0) < 0.01

    def test_evaluar_producto_fijo_con_tipo(self):
        p = Producto(sku="T3", price_type="FIJO", list_price=0.0, fixed_price=30.0)
        p = evaluar_producto(p)
        assert p.price_type == "FIJO"
        assert p.net_price == 30.0

    def test_calcular_cascada_detalle(self):
        result = calcular_cascada(100.0, [0.25, 0.04])
        assert result["descuento_total_pct"] > 0
        assert len(result["pasos"]) == 2
        assert result["pasos"][0]["nivel"] == 1


class TestSkuMatcher:
    def test_cruzar_stock(self):
        maestro = {
            "A1": Producto(sku="A1", description="Prod A", line="VINIBALL", list_price=100.0),
            "A2": Producto(sku="A2", description="Prod B", line="VINIFAN", list_price=80.0),
        }
        stock = {"A1": {"stock": 50, "descripcion": "Prod A"}, "X1": {"stock": 10, "descripcion": "Desconocido"}}
        productos, pendientes = cruzar_stock_con_maestro(stock, maestro)
        assert len(productos) == 2
        assert len(pendientes) == 1
        assert pendientes[0].sku == "X1"

    def test_filtrar_con_stock(self):
        prods = [
            Producto(sku="A", stock=10),
            Producto(sku="B", stock=0),
            Producto(sku="C", stock=5),
        ]
        result = filtrar_con_stock(prods)
        assert len(result) == 2

    def test_segmentar_por_linea(self):
        prods = [
            Producto(sku="1", line="VINIBALL"),
            Producto(sku="2", line="VINIFAN"),
            Producto(sku="3", line="VINIBALL"),
        ]
        seg = segmentar_por_linea(prods)
        assert len(seg["VINIBALL"]) == 2
        assert len(seg["VINIFAN"]) == 1

    def test_depurar_por_capas(self):
        maestro = {
            "A1": Producto(sku="A1", description="P1", list_price=100.0),
            "A2": Producto(sku="A2", description="P2", list_price=0.0),
        }
        stock = {"A1": {"stock": 10, "descripcion": "P1"}}
        activos, pendientes, stats = depurar_por_capas(stock, maestro)
        assert stats["total_erp"] == 1
        assert stats["cruzados_maestro"] == 2


class TestDiffEngine:
    def test_diff_producto_cambio_precio(self):
        p1 = Producto(sku="X1", list_price=100.0)
        p2 = Producto(sku="X1", list_price=120.0)
        diffs = diff_producto(p1, p2)
        campos = [d.campo for d in diffs]
        assert "list_price" in campos

    def test_diff_producto_sin_cambios(self):
        p1 = Producto(sku="X1", list_price=100.0)
        p2 = Producto(sku="X1", list_price=100.0)
        diffs = diff_producto(p1, p2)
        assert len(diffs) == 0

    def test_diff_maestro_nuevo(self):
        old = {"A1": Producto(sku="A1")}
        new = {"A1": Producto(sku="A1"), "B1": Producto(sku="B1")}
        diffs = diff_maestro_completo(old, new)
        assert any(d.es_nuevo for d in diffs)

    def test_diff_maestro_eliminado(self):
        old = {"A1": Producto(sku="A1"), "B1": Producto(sku="B1")}
        new = {"A1": Producto(sku="A1")}
        diffs = diff_maestro_completo(old, new)
        assert any(d.es_eliminado for d in diffs)

    def test_es_diferente_float(self):
        assert _es_diferente(100.0, 100.0001) is True
        assert _es_diferente(100.0, 100.00001) is False

    def test_es_diferente_lista(self):
        assert _es_diferente([0.25], [0.25]) is False
        assert _es_diferente([0.25], [0.30]) is True


class TestSmartParser:
    def test_extraer_descuentos_short_row(self):
        from src.core.parsers.smart_parser import _extraer_descuentos
        col_map = {"desc1": 2, "desc2": 3, "desc3": 5}
        row = ["SKU1", "Prod", "25"]
        result = _extraer_descuentos(row, col_map)
        assert len(result) == 1
        assert result[0] == 0.25

    def test_extraer_descuentos_empty_row(self):
        from src.core.parsers.smart_parser import _extraer_descuentos
        col_map = {"desc1": 5, "desc2": 6}
        row = ["SKU1"]
        result = _extraer_descuentos(row, col_map)
        assert result == []

    def test_match_keyword_exact(self):
        from src.core.parsers.common import match_keyword
        assert match_keyword("CÓDIGO", "CÓDIGO") is True

    def test_match_keyword_abbreviation(self):
        from src.core.parsers.common import match_keyword
        assert match_keyword("COD", "COD") is True
        assert match_keyword("CÓD", "CÓD") is True

    def test_match_keyword_no_false_positive(self):
        from src.core.parsers.common import match_keyword
        assert match_keyword("DESCONOCIDO", "COD") is False

    def test_match_keyword_abbreviation_suffix(self):
        from src.core.parsers.common import match_keyword
        assert match_keyword("CÓDIGO", "CÓD") is True
        assert match_keyword("CATEGORIA", "CAT") is True

    def test_detectar_columnas_basic(self):
        from src.core.parsers.common import detectar_columnas
        headers = ["N°", "CÓDIGO", "ARTÍCULO", "P. LISTA", "D1", "D2", "D3"]
        cmap = detectar_columnas(headers)
        assert "sku" in cmap
        assert "description" in cmap
        assert "list_price" in cmap
        assert "desc1" in cmap


class TestStockDownloader:
    def test_detect_column_map_backward_search(self):
        from src.core.parsers.stock_downloader import _detect_column_map
        filas = [
            ["", "CÓDIGO", "ARTÍCULO", "", "", "", "", "", "ALMACÉN", "", "", "", "U.M.", "STOCK", "", "", "PREDESPACHO", "", "DISPONIBLE"],
            ["", "SKU1", "Product 1", "", "", "", "", "", "ALM1", "", "", "", "UND", "10", "", "", "0", "", "10"],
        ]
        col_map, header_row, found = _detect_column_map(filas)
        assert found is True
        assert "sku" in col_map
        assert "stock" in col_map
        assert col_map["sku"] < col_map["description"]

    def test_detect_column_map_fallback(self):
        from src.core.parsers.stock_downloader import _detect_column_map
        filas = [["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]]
        col_map, header_row, found = _detect_column_map(filas)
        assert found is False
        assert "sku" in col_map
