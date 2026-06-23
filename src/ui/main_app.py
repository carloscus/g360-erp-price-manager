import copy
import json

import flet as ft
from src.ui.theme import (
    build_colors_dict, set_theme, is_dark, rgba, safe_page, text_primary, accent, warning,
    F_TINY, F_SMALL, F_NORMAL, F_MEDIUM, F_LARGE, F_TITLE
)
from src.ui.state_manager import AppState
from src.ui.sidebar import G360Sidebar
from src.ui.components.status_panel import StatusPanel
from src.ui.views import ListaPreciosView
from src.ui.views.configuracion_view import ConfiguracionView
from src.ui.views.actualizar_datos_view import ActualizarDatosView
from src.core.models import Producto, PricingRules, ListaPrecio, DescuentosCategoria, crear_listas_simuladas
from src.core.catalogo_maestro import CatalogoMaestro
from src.core.maestro_comercial import MaestroComercial
from src.core.engine.price_engine import evaluar_lote
from src.core.engine.sku_matcher import depurar_por_capas
from src.core.parsers.source_manager import SourceManager
from src.core.parsers.stock_downloader import download_stock
from src.core.parsers.xls_fallback import leer_xls_fallback
from src.core.parsers.smart_parser import parsear_fuente
from src.core.constants import WINDOW_WIDTH, WINDOW_HEIGHT, APP_TITLE, APP_NAME, MAESTRO_FILE, SAMPLES_DIR, PRICING_RULES_FILE

# ── REFACTOR: On-Demand (Carga Bajo Demanda) ────────────────────────
# La vista refactorizada usa LazyDataManager para cargar solo la
# categoria seleccionada en la tabla, evitando renderizar todos
# los productos simultaneamente (>14,000 registros).
from src.core.lazy_data_manager import LazyDataManager
from src.ui.views.lista_precios_view_refactored import ListaPreciosViewRefactored


class G360ErpPriceList:
    def __init__(self, page: ft.Page):
        self.page = page
        self.app_state = AppState()
        self.app_state.page = page
        self.colors = build_colors_dict()
        self.catalogo = CatalogoMaestro()
        self.pricing_rules = PricingRules()
        self.maestro_comercial = MaestroComercial()
        self.source_manager = SourceManager()
        self._stock_dict: dict = {}

        self.app_state.listas = crear_listas_simuladas()
        self._load_pricing_rules()
        self.maestro_comercial.cargar()

        # ── REFACTOR: LazyDataManager (Carga Bajo Demanda) ────────────
        self.lazy_manager = LazyDataManager()
        self._use_refactored_view = True  # Vista limpia: una categoria por vez

        self._views = [None] * 3
        self._p2_skus: set[str] = set()
        self._data_version = 0
        self._view_versions = [0] * 3
        self._prev_view_idx: int | None = None
        self._data_changed = False
        self._needs_update = False

        self.app_state.subscribe("productos", self._on_productos_changed)
        self.app_state.subscribe("status_message", self._on_status_changed)
        self.app_state.subscribe("traductor", self._on_traductor_changed)
        self.app_state.subscribe("current_view", self._on_current_view_changed)

        self._setup_page()
        self._init_components()
        self.sidebar.restore_state(self.page)
        self._build_ui()
        
        # Carga automática inicial
        self.page.run_thread(self._try_auto_load)

    def _setup_page(self):
        dark = self.app_state.dark_mode
        self.page.title = APP_TITLE
        self.page.window.width = WINDOW_WIDTH
        self.page.window.height = WINDOW_HEIGHT
        self.page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        self.page.bgcolor = self.colors["bg_dark"]
        self.page.padding = 0
        self.page.window.resizable = True
        
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                surface=self.colors["surface_light"],
                on_surface=self.colors["text_primary"],
            ),
            visual_density=ft.VisualDensity.COMPACT,
        )

    def _init_components(self):
        self.sidebar = G360Sidebar(
            on_nav_change=self._on_nav_change,
            colors=self.colors,
            on_theme_toggle=self._on_theme_toggle,
        )
        self.status_panel = StatusPanel(self.colors)

        self._stack_controls: list[ft.Container] = []
        self.content_stack = ft.Stack(expand=True)
        self.content_area = ft.Container(
            content=self.content_stack,
            expand=True,
        )

        self.top_bar_divider = ft.Container(width=1, height=24, bgcolor=self.colors["border"])
        self.top_bar = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Image(src="assets/images/Logo_cipsa_solid.png", width=28, height=28, fit="contain"),
                    self.top_bar_divider,
                    ft.Text("Price Manager", size=F_LARGE, weight=ft.FontWeight.W_800, color=self.colors["accent"]),
                    ft.Text("v1.0", size=F_TINY, color=self.colors["text_muted"], weight=ft.FontWeight.W_300),
                ], spacing=10, vertical_alignment="center"),
                ft.Container(expand=True),
                self.status_panel.get_control(),
            ], alignment="spaceBetween", vertical_alignment="center"),
            padding=ft.Padding(left=16, top=10, right=16, bottom=10),
            bgcolor=rgba(self.colors["surface"], 0.5),
            border=ft.Border(bottom=ft.BorderSide(1, self.colors["border"])),
        )

    def _build_ui(self):
        self._main_content = ft.Container(
            content=ft.Column([self.content_area], expand=True, scroll="auto"),
            expand=True, padding=16, bgcolor=self.colors["bg_dark"],
        )
        self._layout_divider = ft.VerticalDivider(width=1, color=self.colors["border"])
        self.page.add(
            ft.Column([
                self.top_bar,
                ft.Row([
                    self.sidebar.container,
                    self._layout_divider,
                    self._main_content,
                ], expand=True),
            ], expand=True),
        )

    def _load_pricing_rules(self):
        try:
            if PRICING_RULES_FILE.exists():
                with open(PRICING_RULES_FILE, "r", encoding="utf-8") as f:
                    self.pricing_rules = PricingRules.from_dict(json.load(f))
        except Exception:
            self.pricing_rules = PricingRules()

    def _save_pricing_rules(self):
        PRICING_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PRICING_RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.pricing_rules.to_dict(), f, ensure_ascii=False, indent=2)

    def _try_auto_load(self):
        if self.app_state.is_loading:
            return
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Cargando datos del ERP...")
        try:
            self._load_erp_base()
            self._download_and_merge_stock()
            self.catalogo.guardar()
            self._finalize_display(
                status_msg=f"ERP: {len(self.catalogo.productos)} productos cargados",
                status_level="success"
            )
            print(f"[DEBUG] UI actualizada")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.status_panel.set_status(f"Error cargando: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    def _load_erp_base(self):
        from src.core.parsers.xls_fallback import leer_xls_fallback
        from src.core.parsers.smart_parser import parsear_fuente
        base_path = SAMPLES_DIR / "base_catalogo.xls"
        print(f"[DEBUG] Buscando base_catalogo en: {base_path}")
        if not base_path.exists():
            print(f"[DEBUG] No existe base_catalogo.xls")
            return
        filas = leer_xls_fallback(str(base_path))
        if not filas:
            return
        fuente = parsear_fuente(filas, "base_catalogo.xls")
        print(f"[DEBUG] Productos parseados de base: {len(fuente.productos)}")
        if fuente.productos:
            merge_result = self.source_manager.reemplazar_maestro(fuente)
            for p in merge_result.productos:
                self.catalogo.upsert(p)
            self.status_panel.set_status(f"ERP: {len(fuente.productos)} productos cargados", "success")
        else:
            print(f"[DEBUG] base_catalogo.xls no devolvió productos. Errores: {fuente.errores}")
            self.status_panel.set_status("base_catalogo.xls vacío o malformado", "warning")

    def _download_and_merge_stock(self):
        from src.core.parsers.stock_downloader import download_stock
        from src.core.engine.sku_matcher import depurar_por_capas
        self.status_panel.set_loading(True, "Descargando stock...")
        print(f"[DEBUG] Descargando stock desde appweb...")
        stock = download_stock()
        if not stock:
            print(f"[DEBUG] Falló la descarga de stock o vino vacío. Usando catálogo sin stock.")
            self.status_panel.set_status("Error descargando stock (usando catálogo base)", "warning")
            return
        print(f"[DEBUG] Stock descargado para {len(stock)} SKUs")
        for sku, info in stock.items():
            if sku in self.catalogo.productos:
                p = self.catalogo.productos[sku]
                p.stock = info.get("stock", 0)
                p.pre_dispatch = info.get("predespacho", 0)
                if "almacenes" in info:
                    p.warehouse_stock = info["almacenes"]
                p.stock_status = "AGOTADO" if p.stock <= 0 else ("BJ" if p.stock <= 3 else "OK")
        activos, _, stock_stats = depurar_por_capas(stock, self.catalogo.productos)
        print(f"[DEBUG] SKUs activos tras cruce: {len(activos)}")
        self.status_panel.set_status(f"Stock: {stock_stats['activos']}/{stock_stats['total_erp']} SKUs activos", "success")

    def _load_inventario_cache(self):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Cargando catálogo en caché...")
        try:
            n = self.catalogo.cargar()
            if n == 0:
                self.status_panel.set_status("Caché vacío, recargando desde fuentes...", "warning")
                self.page.run_thread(self._load_inventario_full)
                return
            self.status_panel.set_loading(True, "Descargando stock...")
            self._refresh_stock_from_cache()
            meta = self.catalogo._metadata
            ts = meta.get("cached_at", "")
            self.app_state.current_view = 2
            self.sidebar.nav_rail.selected_index = 2
            self._finalize_display(
                status_msg=f"Catálogo: {n} productos {f'(desde {ts[:10]})' if ts else ''} — stock refrescado",
                status_level="success",
            )
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.status_panel.set_status(f"Error cargando caché: {ex}, recargando...", "error")
            self.page.run_thread(self._load_inventario_full)
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    @staticmethod
    def _apply_stock_info(producto: Producto, info: dict):
        producto.stock = info.get("disponible", info.get("stock", 0))
        producto.pre_dispatch = info.get("predespacho", 0)
        if "almacenes" in info and info["almacenes"]:
            existing = producto.warehouse_stock or {}
            for alm_key, vals in info["almacenes"].items():
                if alm_key in existing and isinstance(existing[alm_key], list):
                    existing[alm_key][0] = vals[0] if isinstance(vals, list) else vals
                    existing[alm_key][1] = vals[1] if isinstance(vals, list) and len(vals) > 1 else 0
                else:
                    existing[alm_key] = vals if isinstance(vals, list) else [vals, 0]
            producto.warehouse_stock = existing
        producto.stock_status = "AGOTADO" if producto.stock <= 0 else ("BJ" if producto.stock <= 3 else "OK")

    def _merge_stock_to_catalogo(self, stock: dict[str, dict]):
        for sku, info in stock.items():
            if sku in self.catalogo.productos:
                self._apply_stock_info(self.catalogo.productos[sku], info)

    def _refresh_stock_from_cache(self):
        try:
            stock = download_stock()
            if stock:
                self._merge_stock_to_catalogo(stock)
        except Exception:
            pass

    def _load_inventario_full(self):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Cargando datos del ERP...")
        try:
            base_path = SAMPLES_DIR / "base_catalogo.xls"
            if base_path.exists():
                filas = leer_xls_fallback(str(base_path))
                if filas:
                    fuente = parsear_fuente(filas, "base_catalogo.xls")
                    if fuente.productos:
                        merge_result = self.source_manager.reemplazar_maestro(fuente)
                        for p in merge_result.productos:
                            p.catalog_price = p.list_price
                            self.catalogo.upsert(p)

            self.status_panel.set_loading(True, "Descargando stock...")
            try:
                stock = download_stock()
                if stock:
                    self._merge_stock_to_catalogo(stock)
                else:
                    self.status_panel.set_status("Stock no disponible, usando catálogo base", "warning")
            except Exception:
                self.status_panel.set_status("Stock no disponible, usando catálogo base", "warning")

            from datetime import datetime
            self.catalogo._metadata["cached_at"] = datetime.now().isoformat()
            self.catalogo.guardar()
            self.app_state.current_view = 2
            self.sidebar.nav_rail.selected_index = 2
            self._finalize_display(
                status_msg=f"Catálogo: {len(self.catalogo.productos)} productos cargados y cacheados",
                status_level="success",
            )
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.status_panel.set_status(f"Error cargando: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    def _load_plantilla(self, path: str):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Cargando plantilla de precios...")
        try:
            from src.core.parsers.plantilla_parser import parsear_plantilla_precios
            plant_productos, pendientes, stats = parsear_plantilla_precios(path)
            divergentes = 0
            for p in plant_productos:
                if p.sku in self.catalogo.productos:
                    existing = self.catalogo.productos[p.sku]
                    old_price = existing.list_price
                    existing.list_price = p.list_price
                    if old_price != p.list_price and old_price > 0:
                        existing.catalog_price = old_price
                        existing.precio_divergente = True
                        divergentes += 1
                    if not existing.units_per_box or existing.units_per_box == 1:
                        existing.units_per_box = p.units_per_box
                    if not existing.description and p.description:
                        existing.description = p.description
                    if not existing.ean13 and p.ean13:
                        existing.ean13 = p.ean13
                    if not existing.weight_kg and p.weight_kg:
                        existing.weight_kg = p.weight_kg
                    if not existing.line and p.line:
                        existing.line = p.line
                    if p.commercial_discounts:
                        existing.commercial_discounts = p.commercial_discounts
                    if p.additional_discounts:
                        existing.additional_discounts = p.additional_discounts
                    if p.rebate_override > 0:
                        existing.rebate_override = p.rebate_override
                    if p.special_override > 0:
                        existing.special_override = p.special_override
                    if p.price_type == 'FIJO' and p.fixed_price:
                        existing.price_type = 'FIJO'
                        existing.fixed_price = p.fixed_price
                else:
                    p.catalog_price = p.list_price
                    self.catalogo.upsert(p)
            self.catalogo.guardar()
            self.app_state.productos = list(self.catalogo.productos.values())
            self._reapply_discounts_and_refresh()
            self.status_panel.set_status(
                f"Plantilla: {len(plant_productos)} productos{', ' + str(divergentes) + ' precios divergentes' if divergentes else ''}",
                "warning" if divergentes else "success")
        except Exception as ex:
            self.status_panel.set_status(f"Error cargando plantilla: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    def _preload_samples(self, catalogo_path: str):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Precargando datos de ejemplo...")
        try:
            filas = leer_xls_fallback(catalogo_path)
            if filas:
                fuente = parsear_fuente(filas, "base_catalogo.xls")
                if fuente.productos:
                    merge_result = self.source_manager.reemplazar_maestro(fuente)
                    for p in merge_result.productos:
                        self.catalogo.upsert(p)

            stock = download_stock()
            if stock:
                self._merge_stock_to_catalogo(stock)
                self._finalize_display(
                    status_msg=f"Ejemplo: {len(stock)} SKU con stock cargados",
                    status_level="success",
                )
                return

            self._finalize_display(
                status_msg="Catálogo base cargado (sin stock)",
                status_level="warning",
            )
        except Exception as ex:
            self.status_panel.set_status(f"Error precargando: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    def _load_maestro(self):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Cargando catálogo...")
        try:
            n = self.catalogo.cargar()
            self._finalize_display(
                status_msg=f"Catálogo cargado: {n} productos",
                status_level="success",
            )
        except Exception as ex:
            self.status_panel.set_status(f"Error: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    def _on_file_loaded(self, path: str, name: str):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, f"Importando {name}...")
        self.page.run_thread(self._import_file, path, name)

    def _import_file(self, path: str, name: str):
        try:
            fuente = self.source_manager.importar_archivo(path)
            if fuente.errores:
                self.status_panel.set_status(f"Errores: {'; '.join(fuente.errores[:3])}", "error")
                return

            if name.lower().endswith(".json"):
                import json
                from pathlib import Path
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                prods_raw = data.get("productos", data if isinstance(data, list) else [])
                productos = [Producto.from_dict(d) for d in prods_raw]
                for p in productos:
                    self.catalogo.upsert(p)
            else:
                merge_result = self.source_manager.merge_al_maestro(fuente)
                for p in merge_result.productos:
                    self.catalogo.upsert(p)

            productos = list(self.catalogo.productos.values())
            productos = evaluar_lote(productos)
            self.app_state.productos = productos
            self.app_state.catalogo = {p.sku: p.to_dict() for p in productos}
            self.status_panel.set_status(f"{len(productos)} SKUs", "success")
            self.status_panel.set_status(f"Importado: {fuente.total_rows} productos", "success")
            self._update_content()
        except Exception as ex:
            self.status_panel.set_status(f"Error importando: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)

    def _on_download_stock(self):
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Descargando stock...")
        self.page.run_thread(self._download_stock_thread)

    def _download_stock_thread(self):
        try:
            stock = download_stock()
            if stock is None:
                self.status_panel.set_status("Error descargando stock", "error")
                return
            self._stock_dict = stock
            self._merge_stock_to_catalogo(stock)
            self._finalize_display(status_msg=f"Stock descargado: {len(stock)} SKUs", status_level="success")
        except Exception as ex:
            self.status_panel.set_status(f"Error: {ex}", "error")

    def _finalize_display(self, status_msg=None, status_level="success", switch_to_view=None):
        productos = []
        for prod in self.catalogo.productos.values():
            p = copy.deepcopy(prod)
            self.pricing_rules.apply_to(p)
            productos.append(p)
        productos = self.maestro_comercial.aplicar_a(productos)

        productos = self._aplicar_descuentos_por_categoria(productos)
        productos = evaluar_lote(productos)

        self.app_state.productos = productos
        self.app_state.catalogo = {p.sku: p.to_dict() for p in productos}
        self.app_state.productos_p2 = list(productos)

        # ── REFACTOR: Poblar LazyDataManager (carga bajo demanda) ────
        self.lazy_manager.cargar_productos(productos)

        lineas = sorted(set(p.line for p in productos if p.line))
        self.app_state.lineas = lineas
        self.status_panel.set_status(f"{len(productos)} SKUs", "success")

        categorizados = sum(1 for p in productos if p.category)
        self.app_state.pendientes = {
            "total": len(self.catalogo.productos),
            "categorizados": categorizados,
            "sin_categoria": len(self.catalogo.productos) - categorizados,
            "con_stock": sum(1 for p in productos if p.stock > 0),
            "con_precio": sum(1 for p in productos if p.list_price > 0),
            "divergentes": sum(1 for p in productos if getattr(p, "precio_divergente", False)),
        }

        if switch_to_view is not None:
            self.app_state.current_view = switch_to_view
            self.sidebar.nav_rail.selected_index = switch_to_view

        self._update_content()
        self._prebuild_all_views()

        if status_msg:
            self.status_panel.set_status(status_msg, status_level)
        self.app_state.is_loading = False
        self.status_panel.set_loading(False)

    def _crear_vista_lista_precios(self):
        """Factory method: retorna ListaPreciosViewRefactored o ListaPreciosView segun flag."""
        if self._use_refactored_view:
            return ListaPreciosViewRefactored(
                self.colors, lazy_manager=self.lazy_manager,
                state=self.app_state,
                on_file_loaded=self._on_file_loaded,
                on_desc_quick_apply=self._on_desc_quick_apply,
                on_toggle_almacen=self._on_toggle_almacen,
                on_cell_edit=self._on_cell_edit,
                on_selection_change=self._on_selection_change,
                on_page_change=self._on_page_change_view,
                on_lista_select=self._on_lista_select,
                on_export_json=self._on_export,
                on_export_xlsx=self._on_export_xlsx,
                on_save_cliente_list=self._on_save_cliente_list,
                on_export_xlsx_formulas=self._on_export_xlsx_formulas,
            )
        return ListaPreciosView(
            self.colors, state=self.app_state,
            on_file_loaded=self._on_file_loaded,
            on_desc_quick_apply=self._on_desc_quick_apply,
            on_toggle_almacen=self._on_toggle_almacen,
            on_cell_edit=self._on_cell_edit,
            on_selection_change=self._on_selection_change,
            on_page_change=self._on_page_change_view,
            on_lista_select=self._on_lista_select,
            on_export_json=self._on_export,
            on_export_xlsx=self._on_export_xlsx,
            on_save_cliente_list=self._on_save_cliente_list,
        )

    def _prebuild_all_views(self):
        """Build all views after data load so tab switches are instant."""
        for idx in range(3):
            if self._view_versions[idx] == self._data_version:
                continue  # already built
            try:
                if idx == 0:
                    if self._views[0] is None:
                        self._views[0] = self._crear_vista_lista_precios()
                    view = self._views[0]
                elif idx == 1:
                    if self._views[1] is None:
                        self._views[1] = ConfiguracionView(
                            self.colors, state=self.app_state,
                            on_cell_edit=self._on_cell_edit,
                            on_category_assigned=self._on_category_assigned,
                            on_units_per_box_change=self._on_units_per_box_change,
                        )
                    view = self._views[1]
                else:
                    if self._views[2] is None:
                        self._views[2] = ActualizarDatosView(
                            self.colors, state=self.app_state, app=self,
                        )
                    view = self._views[2]
                built = view.build()
                self._set_stack_view(idx, built)
                self._view_versions[idx] = self._data_version
            except Exception as ex:
                import traceback; traceback.print_exc()
                err = ft.Container(
                    content=ft.Column([
                        ft.Text(f"Error precargando vista {idx}: {ex}", color="red", size=14),
                        ft.Text(traceback.format_exc(), color="red", size=9, font_family="monospace"),
                    ], scroll=ft.ScrollMode.AUTO),
                    padding=20, expand=True,
                )
                self._set_stack_view(idx, err)
                self._view_versions[idx] = self._data_version

    def _reapply_discounts_and_refresh(self):
        if not self.app_state.productos:
            return
        productos = self._aplicar_descuentos_por_categoria(self.app_state.productos)
        productos = evaluar_lote(productos)
        self.app_state.productos = list(productos)
        self.app_state.productos_p2 = list(productos)
        self.app_state.catalogo = {p.sku: p.to_dict() for p in productos}
        self._update_content()

    def _aplicar_descuentos_por_categoria(self, productos: list) -> list:
        from src.core.config_manager import config_manager
        lista_activa_id = self.app_state.lista_activa
        listas = self.app_state.listas
        if not lista_activa_id or lista_activa_id not in listas:
            for p in productos:
                if not p._dc_ref and not p.has_overrides():
                    defaults = config_manager.default_discounts.get(p.category, [])
                    if defaults:
                        p.discount_chain = defaults
            return productos
        lista = listas[lista_activa_id]
        for p in productos:
            cat_key = p.category or p.line
            dc = lista.discounts_by_category.get(cat_key)
            if dc:
                p._dc_ref = dc
                p._dc_ref_category = dc.category
            else:
                p._dc_ref = None
                p._dc_ref_category = None
                if not p.has_overrides():
                    p.discount_chain = lista.get_discounts_for_category(cat_key)
        return productos

    def _on_desc_change(self, lista_id: str, cat: str, descuentos: list, fijos: list, rebate: float = 0.0, especial: float = 0.0, especial_label: str = ""):
        listas = self.app_state.listas
        if lista_id not in listas:
            return
        lista = listas[lista_id]
        if cat in lista.discounts_by_category:
            lista.discounts_by_category[cat].discounts = descuentos
            lista.discounts_by_category[cat].fixed_discounts = fijos
            lista.discounts_by_category[cat].rebate = rebate
            lista.discounts_by_category[cat].special_discount = especial
            lista.discounts_by_category[cat].special_label = especial_label
        else:
            lista.discounts_by_category[cat] = DescuentosCategoria(
                category=cat, discounts=descuentos, fixed_discounts=fijos,
                rebate=rebate, special_discount=especial, special_label=especial_label,
            )
        current = self.app_state.listas
        current[lista_id] = lista
        self.app_state.listas = current
        if self.app_state.lista_activa == lista_id and self.app_state.productos:
            self._reapply_discounts_and_refresh()
            rebate_str = f"+R{int(rebate*100)}" if rebate else ""
            esp_str = f"+{especial_label}{int(especial*100)}" if especial else ""
            self.status_panel.set_status(
                f"{lista.name}: {cat} → {'-'.join(str(int(d*100)) for d in descuentos) if descuentos else 'sin'}"
                f"+{'-'.join(str(int(f*100)) for f in fijos) if fijos else '0'}{rebate_str}{esp_str}",
                "accent"
            )

    def _on_nav_change(self, e):
        idx = e.control.selected_index
        self.app_state.current_view = idx

    def _on_theme_toggle(self, dark: bool):
        self.app_state.dark_mode = dark
        set_theme(dark)
        self.colors = build_colors_dict(dark)
        self.page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        self.page.bgcolor = self.colors["bg_dark"]
        self.top_bar.bgcolor = rgba(self.colors["surface"], 0.5)
        self.top_bar.border = ft.Border(bottom=ft.BorderSide(1, self.colors["border"]))
        self.top_bar_divider.bgcolor = self.colors["border"]
        self._rebuild_layout_bg()
        self.sidebar.refresh_theme(self.colors)
        self.status_panel.refresh_colors(self.colors)
        self._views = [None] * 3
        self._view_versions = [0] * 3
        self._data_version += 1
        self._update_content()
        self.page.update()

    def _rebuild_layout_bg(self):
        try:
            self._main_content.bgcolor = self.colors["bg_dark"]
            self._layout_divider.color = self.colors["border"]
            if safe_page(self._main_content):
                self._main_content.update()
        except Exception:
            pass

    def _on_current_view_changed(self, state: AppState):
        idx = state.current_view
        if self.sidebar.nav_rail.selected_index != idx:
            self.sidebar.nav_rail.selected_index = idx
            self.sidebar.nav_rail.update()
        
        self.sidebar.save_state(self.page, idx)
        self._update_content()

    def _on_productos_changed(self, state: AppState):
        self._data_version += 1
        self._data_changed = True
        if state.productos:
            lineas = sorted(set(p.line for p in state.productos if p.line))
            state.lineas = lineas
            cats = set(p.category for p in state.productos if p.category)
            if cats and not state.categorias_activas:
                state.categorias_activas = cats

    def _on_traductor_changed(self, state: AppState):
        self._run_ui_update(self._actualizar_vista())

    def _on_status_changed(self, state: AppState):
        self.status_panel.set_status(state.status_message, state.status_level)

    def _update_content(self):
        view_idx = self.app_state.current_view
        try:
            if view_idx == 0:
                if self._views[0] is None:
                    self._views[0] = self._crear_vista_lista_precios()
                view = self._views[0]
            elif view_idx == 1:
                if self._views[1] is None:
                    self._views[1] = ConfiguracionView(
                        self.colors, state=self.app_state,
                        on_cell_edit=self._on_cell_edit,
                        on_category_assigned=self._on_category_assigned,
                        on_units_per_box_change=self._on_units_per_box_change,
                    )
                view = self._views[1]
            elif view_idx == 2:
                if self._views[2] is None:
                    self._views[2] = ActualizarDatosView(
                        self.colors, state=self.app_state, app=self,
                    )
                view = self._views[2]
            else:
                view = ft.Container(content=ft.Text(f"Vista {view_idx} no existe", color="red"), padding=20)

            if isinstance(view, ft.Container):
                self._set_stack_view(view_idx, view)
                self._needs_update = True
            elif (view_idx != self._prev_view_idx
                  and view_idx < len(self._stack_controls)
                  and self._view_versions[view_idx] == self._data_version):
                for i, ctl in enumerate(self._stack_controls):
                    ctl.visible = (i == view_idx)
                    try:
                        ctl.update()
                    except RuntimeError:
                        pass
                self._needs_update = False
            else:
                built = view.build()
                self._set_stack_view(view_idx, built)
                self._view_versions[view_idx] = self._data_version
                self._needs_update = True

            if self._needs_update and self.content_area.page:
                self.content_stack.update()

            self._prev_view_idx = view_idx
        except Exception as ex:
            import traceback; traceback.print_exc()
            err = ft.Container(
                content=ft.Column([
                    ft.Text(f"Error al mostrar vista {view_idx}: {ex}", color="red", size=14),
                    ft.Text(traceback.format_exc(), color="red", size=9, font_family="monospace"),
                ], scroll=ft.ScrollMode.AUTO),
                padding=20, expand=True,
            )
            self._set_stack_view(view_idx, err)

    def _set_stack_view(self, idx: int, content: ft.Control):
        while len(self._stack_controls) <= idx:
            c = ft.Container(visible=False, expand=True)
            self._stack_controls.append(c)
            self.content_stack.controls.append(c)
        wrapper = ft.Container(content=content, expand=True, visible=(idx == self.app_state.current_view))
        self._stack_controls[idx] = wrapper
        self.content_stack.controls[idx] = wrapper

    def _on_export(self):
        self.page.run_thread(self._export_thread)

    def _on_export_xlsx(self):
        self.page.run_thread(self._export_xlsx_thread)

    def _on_export_xlsx_formulas(self, productos: list, categoria: str, dc):
        self.page.run_thread(self._export_xlsx_formulas_thread, productos, categoria, dc)

    def _export_xlsx_formulas_thread(self, productos: list, categoria: str, dc):
        try:
            from src.core.xlsx_generator import generar_xlsx_categoria_formulas
            import shutil, os
            from pathlib import Path
            path = generar_xlsx_categoria_formulas(productos, categoria, dc)
            if path:
                desktop = Path(os.path.expanduser("~")) / "Desktop"
                desktop.mkdir(exist_ok=True)
                dest = desktop / Path(path).name
                shutil.copy2(path, dest)
                os.startfile(str(dest))
                self.status_panel.set_status(f"XLSX abierto: {dest.name}", "success")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.status_panel.set_status(f"Error XLSX formulas: {ex}", "error")

    def _export_thread(self):
        try:
            from src.core.json_generator import generar_json_maestro
            path = generar_json_maestro(list(self.catalogo.productos.values()))
            self.status_panel.set_status(f"Exportado: {path}", "success")
        except Exception as ex:
            self.status_panel.set_status(f"Error exportando: {ex}", "error")

    def _export_xlsx_thread(self):
        try:
            from src.core.xlsx_generator import generar_xlsx_lista
            cat_activas = self.app_state.categorias_activas or set()
            p2 = self.app_state.productos_p2 or self.app_state.productos or []
            path = generar_xlsx_lista(
                list(p2),
                cat_activas,
            )
            self.status_panel.set_status(f"XLSX generado: {path}", "success")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.status_panel.set_status(f"Error exportando XLSX: {ex}", "error")

    def _on_save_cliente_list(self, cliente: str, categorias: list[str]):
        self.page.run_thread(self._save_cliente_list_thread, cliente, categorias)

    def _save_cliente_list_thread(self, cliente: str, categorias: list[str]):
        from src.core.xlsx_generator import generar_xlsx_cliente
        from src.core.json_generator import generar_json_cliente, actualizar_perfil_cliente
        ok = 0
        productos = self.app_state.productos_p2 or self.app_state.productos or []
        for cat in categorias:
            try:
                xlsx_path = generar_xlsx_cliente(list(productos), cat, cliente)
                if xlsx_path:
                    generar_json_cliente(list(productos), cat, cliente)
                    ok += 1
            except Exception as ex:
                import traceback; traceback.print_exc()
        try:
            actualizar_perfil_cliente(cliente, list(productos))
        except Exception as ex:
            import traceback; traceback.print_exc()
        if ok:
            cl = cliente.strip()
            self.status_panel.set_status(f"{ok} archivos guardados en listas/{cl}/", "success")
        else:
            self.status_panel.set_status("No se generaron archivos (verificar categor\u00edas)", "warning")

    def _on_lista_save(self, nombre: str, values: dict):
        lid = nombre.lower().replace(" ", "_")
        discounts_by_category = {}
        for cat, vals in values.items():
            commercial_discounts = vals.get("commercial_discounts", vals.get("comerciales", [])) if isinstance(vals, dict) else vals
            fixed = vals.get("fixed", vals.get("fijos", [])) if isinstance(vals, dict) else []
            rebate = float(vals.get("rebate", 0)) if isinstance(vals, dict) else 0.0
            special = float(vals.get("special", vals.get("especial", 0))) if isinstance(vals, dict) else 0.0
            special_label = str(vals.get("special_label", vals.get("especial_label", ""))) if isinstance(vals, dict) else ""
            if isinstance(commercial_discounts, list) and (commercial_discounts or fixed or rebate or special):
                discounts_by_category[cat] = DescuentosCategoria(
                    category=cat, discounts=commercial_discounts, fixed_discounts=fixed,
                    rebate=rebate, special_discount=special, special_label=special_label,
                )
        lista = ListaPrecio(
            id=lid,
            name=nombre,
            discounts_by_category=discounts_by_category,
        )
        self.source_manager.listas[lid] = lista
        current = self.app_state.listas
        current[lid] = lista
        self.app_state.listas = current
        self.app_state.lista_activa = lid
        self.status_panel.set_status(f"Lista '{nombre}' guardada", "success")
        self._reapply_discounts_and_refresh()

    def _on_lista_select(self, lid: str):
        if lid == "__nueva__":
            self.app_state.lista_activa = None
            self.status_panel.set_status("Crear nueva lista", "accent")
        else:
            self.app_state.lista_activa = lid
            nombre = self.app_state.listas[lid].name if lid in self.app_state.listas else lid
            self.status_panel.set_status(f"Lista activa: {nombre}", "accent")
        self._reapply_discounts_and_refresh()

    def _on_desc_quick_apply(self, cat: str, descuentos: list, rebate: float, especial: float, especial_label: str):
        lista_activa_id = self.app_state.lista_activa
        if not lista_activa_id or lista_activa_id not in self.app_state.listas:
            return
        if cat == "__todas__":
            self._reapply_discounts_and_refresh()
            return
        if cat:
            self._on_desc_change(lista_activa_id, cat, descuentos, [], rebate, especial, especial_label)
        else:
            listas = self.app_state.listas
            lista = listas[lista_activa_id]
            for c in lista.discounts_by_category:
                self._on_desc_change(lista_activa_id, c, descuentos, [], rebate, especial, especial_label)

    def _on_toggle_almacen(self, name: str, visible: bool):
        self._update_content()

    def _on_cell_edit(self, sku: str, col_key: str, value: str):
        productos = self.app_state.productos
        producto = next((p for p in productos if p.sku == sku), None)
        if not producto:
            return

        if col_key in ("_d1", "_desc01"):
            producto.commercial_discounts = self._update_disc_level(producto.commercial_discounts, 0, value)
            self.pricing_rules.discounts[sku] = list(producto.commercial_discounts)
            self._save_pricing_rules()
        elif col_key in ("_d2", "_desc02"):
            producto.commercial_discounts = self._update_disc_level(producto.commercial_discounts, 1, value)
            self.pricing_rules.discounts[sku] = list(producto.commercial_discounts)
            self._save_pricing_rules()
        elif col_key in ("_d3", "_desc03"):
            producto.commercial_discounts = self._update_disc_level(producto.commercial_discounts, 2, value)
            self.pricing_rules.discounts[sku] = list(producto.commercial_discounts)
            self._save_pricing_rules()
        elif col_key == "_desc04":
            producto.commercial_discounts = self._update_disc_level(producto.commercial_discounts, 3, value)
            self.pricing_rules.discounts[sku] = list(producto.commercial_discounts)
            self._save_pricing_rules()
        elif col_key == "_rebate":
            producto.rebate_override = self._parse_single_pct(value)
            self.pricing_rules.rebate_overrides[sku] = producto.rebate_override
            self._save_pricing_rules()
        elif col_key == "_custom":
            producto.special_override = self._parse_single_pct(value)
            self.pricing_rules.special_overrides[sku] = producto.special_override
            self._save_pricing_rules()
        elif col_key == "_feria":
            producto.feria_discount = self._parse_single_pct(value)
            if producto.feria_discount > 0:
                self.pricing_rules.feria_discounts[sku] = producto.feria_discount
            else:
                self.pricing_rules.feria_discounts.pop(sku, None)
            self._save_pricing_rules()
        elif col_key == "_evento":
            producto.evento_discount = self._parse_single_pct(value)
            if producto.evento_discount > 0:
                self.pricing_rules.evento_discounts[sku] = producto.evento_discount
            else:
                self.pricing_rules.evento_discounts.pop(sku, None)
            self._save_pricing_rules()
        elif col_key in ("_special", "_especial"):
            producto.special_override = self._parse_single_pct(value)
            self.pricing_rules.special_overrides[sku] = producto.special_override
            self._save_pricing_rules()
        elif col_key == "_special_adjust":
            producto.special_discount_adjust = self._parse_single_pct(value)
            if producto.special_discount_adjust > 0:
                self.pricing_rules.special_adjust[sku] = producto.special_discount_adjust
            else:
                self.pricing_rules.special_adjust.pop(sku, None)
            self._save_pricing_rules()
        elif col_key == "_special_label":
            producto.special_label_override = value
            self.pricing_rules.special_labels[sku] = value
            self._save_pricing_rules()
        elif col_key == "_notes":
            producto.notes = value
            if value:
                self.pricing_rules.notes[sku] = value
            else:
                self.pricing_rules.notes.pop(sku, None)
            self._save_pricing_rules()
        elif col_key == "_sku_cliente":
            producto.customer_sku = value
        elif col_key == "category":
            self._on_category_assigned(sku, value)
            return
            if value:
                self.pricing_rules.categories[sku] = value
                self.maestro_comercial.asignar_categoria(sku, value)
            else:
                self.pricing_rules.categories.pop(sku, None)
                self.maestro_comercial.remover_categoria(sku)
            self.maestro_comercial.guardar()
            self._save_pricing_rules()
        elif col_key == "units_per_box":
            try:
                producto.units_per_box = max(1, int(float(value)))
            except (ValueError, TypeError):
                return
            self.pricing_rules.units_per_box[sku] = producto.units_per_box
            self.maestro_comercial.asignar_units_per_box(sku, producto.units_per_box)
            self.maestro_comercial.guardar()
            self._save_pricing_rules()
        elif col_key == "list_price":
            try:
                producto.list_price = float(value)
            except (ValueError, TypeError):
                return
        elif col_key.startswith("_adic"):
            idx = int(col_key.replace("_adic0", "").replace("_adic", "")) - 1
            pct = self._parse_single_pct(value)
            if not hasattr(producto, "additional_discounts") or not producto.additional_discounts:
                producto.additional_discounts = []
            while len(producto.additional_discounts) <= idx:
                producto.additional_discounts.append(0.0)
            producto.additional_discounts[idx] = pct
            self.pricing_rules.additional_discounts[sku] = list(producto.additional_discounts)
            self._save_pricing_rules()
        elif col_key == "fixed_price":
            try:
                val = float(value)
                if val > 0:
                    producto.price_type = "FIJO"
                    producto.fixed_price = val
                    self.pricing_rules.fixed_prices[sku] = (val, producto.fixed_reason or "")
                else:
                    producto.price_type = "NORMAL"
                    producto.fixed_price = None
                    producto.fixed_reason = ""
                    self.pricing_rules.fixed_prices.pop(sku, None)
            except (ValueError, TypeError):
                return
            self._save_pricing_rules()

        necesita_eval = col_key not in ("_notes", "_special_label", "_sku_cliente")
        if necesita_eval:
            productos = evaluar_lote(productos)
        self.app_state.productos = list(productos)
        self.app_state.productos_p2 = list(productos)
        self.app_state.catalogo = {p.sku: p.to_dict() for p in productos}
        self._update_content()

    def _update_disc_level(self, override_list: list, index: int, value: str) -> list:
        result = list(override_list) if override_list else []
        pct = self._parse_single_pct(value)
        while len(result) <= index:
            result.append(0.0)
        result[index] = pct
        # Trim trailing zeros only
        while result and result[-1] == 0:
            result.pop()
        return result

    def _parse_single_pct(self, value: str) -> float:
        value = value.strip().replace("%", "")
        if not value:
            return 0.0
        try:
            return float(value) / 100
        except ValueError:
            return 0.0

    def _on_selection_change(self, selected_skus: set):
        self.app_state.selected_skus = selected_skus

    def _on_page_change_view(self, page: int):
        self.app_state.pagina = page
        self._update_content()

    def _run_ui_update(self, coro):
        import asyncio, traceback
        try:
            loop = getattr(self.page, 'loop', None)
            if loop is None:
                return
            f = asyncio.run_coroutine_threadsafe(coro, loop)
            f.add_done_callback(lambda fut: fut.exception() and traceback.print_exception(
                type(fut.exception()), fut.exception(), fut.exception().__traceback__))
        except Exception:
            traceback.print_exc()

    def _procesar_catalogo(self, path: str):
        from src.core.parsers.xls_fallback import leer_xls_fallback
        from src.core.parsers.smart_parser import parsear_fuente

        ok = False
        count = 0
        try:
            self.catalogo = CatalogoMaestro()
            filas = leer_xls_fallback(path)
            if filas:
                fuente = parsear_fuente(filas, path)
                if fuente.productos:
                    merge_result = self.source_manager.reemplazar_maestro(fuente)
                    for p in merge_result.productos:
                        self.catalogo.upsert(p)
                count = len(fuente.productos)
                ok = True
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._schedule_status(f"Error catálogo: {ex}", "error")

        if ok:
            self._update_actualizar_status("catalogo", f"{count} productos", accent())
            self._schedule_catalogo_ok(count)
        else:
            self._update_actualizar_status("catalogo", "Error", warning())

    def _schedule_status(self, msg, level):
        self._run_ui_update(self._show_status(msg, level))

    async def _show_status(self, msg, level):
        self.status_panel.set_status(msg, level)
        self.app_state.is_loading = False
        self.status_panel.set_loading(False)

    def _update_actualizar_status(self, key: str, msg: str, color=None):
        async def do_update():
            try:
                v = self._views[2]
                if v and hasattr(v, 'set_file_status'):
                    v.set_file_status(key, msg, color)
            except Exception:
                pass
        self._run_ui_update(do_update())

    def _update_actualizar_stock_status(self, msg: str, color=None):
        async def do_update():
            try:
                v = self._views[2]
                if v and hasattr(v, 'set_stock_status'):
                    v.set_stock_status(msg, color)
            except Exception:
                pass
        self._run_ui_update(do_update())

    def _schedule_catalogo_ok(self, count):
        self._run_ui_update(self._after_catalogo_ok(count))

    async def _after_catalogo_ok(self, count):
        self.status_panel.set_status(f"Catálogo: {count} productos", "success")
        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Descargando stock...")
        self.page.run_thread(self._procesar_stock)

    def _procesar_categorias(self, path: str):
        from src.core.parsers.loaders import cargar_categorias

        try:
            stats = cargar_categorias(path, self.pricing_rules)
            aplicados = stats.get('aplicados', 0)
            self._update_actualizar_status("categorias", f"{aplicados} aplicadas", accent())
            if aplicados > 0:
                self._save_pricing_rules()
                self._finalize_display(
                    status_msg=f"Categorías: {aplicados} SKU actualizados",
                    status_level="success",
                )
            else:
                self._schedule_status("Categorías: 0 aplicadas", "warning")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._update_actualizar_status("categorias", f"Error: {ex}", warning())
            self._schedule_status(f"Error categorías: {ex}", "error")

    def _procesar_descuentos(self, path: str):
        from src.core.parsers.loaders import cargar_descuentos

        try:
            stats = cargar_descuentos(path, self.pricing_rules)
            aplicados = stats.get('aplicados', 0)
            self._update_actualizar_status("descuentos", f"{aplicados} aplicados", accent())
            if aplicados > 0:
                self._save_pricing_rules()
                self._finalize_display(
                    status_msg=f"Descuentos: {aplicados} SKU actualizados",
                    status_level="success",
                )
            else:
                self._schedule_status("Descuentos: 0 aplicados", "warning")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._update_actualizar_status("descuentos", f"Error: {ex}", warning())
            self._schedule_status(f"Error descuentos: {ex}", "error")

    def _procesar_precios_fijos(self, path: str):
        from src.core.parsers.loaders import cargar_precios_fijos

        try:
            stats = cargar_precios_fijos(path, self.pricing_rules)
            aplicados = stats.get('aplicados', 0)
            self._update_actualizar_status("precios_fijos", f"{aplicados} aplicados", accent())
            if aplicados > 0:
                self._save_pricing_rules()
                self._finalize_display(
                    status_msg=f"Precios fijos: {aplicados} SKU actualizados",
                    status_level="success",
                )
            else:
                self._schedule_status("Precios fijos: 0 aplicados", "warning")
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._update_actualizar_status("precios_fijos", f"Error: {ex}", warning())
            self._schedule_status(f"Error precios fijos: {ex}", "error")

    def _procesar_traductor(self, path: str):
        from pathlib import Path
        from src.core.parsers.loaders import cargar_traductor

        try:
            result = cargar_traductor(path)
            mapping = result.get('mapping', {})
            self.pricing_rules.translator.update(mapping)
            self.app_state.traductor = mapping
            fname = Path(path).name
            self.app_state.traductor_file = fname
            self._save_pricing_rules()
            self._update_actualizar_status("traductor", f"{len(mapping)} mapeos", accent())
            self._finalize_display(
                status_msg=f"Traductor: {len(mapping)} mapeos desde {fname}",
                status_level="success",
            )
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._update_actualizar_status("traductor", f"Error: {ex}", warning())
            self._schedule_status(f"Error traductor: {ex}", "error")

    async def _actualizar_vista(self):
        self._update_content()

    def _procesar_stock(self):
        from src.core.parsers.stock_downloader import download_stock

        try:
            stock = download_stock()
            if stock:
                self._apply_stock_data(stock)
            else:
                self._schedule_status("Sin datos de stock", "error")
                self._update_actualizar_stock_status("Sin datos", warning())
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._schedule_status(f"Error stock: {ex}", "error")
            self._update_actualizar_stock_status(f"Error: {ex}", warning())

    def _procesar_stock_file(self, path: str):
        from src.core.parsers.stock_downloader import parse_stock_from_file

        try:
            stock = parse_stock_from_file(path)
            if stock:
                self._apply_stock_data(stock)
            else:
                self._schedule_status("No se pudo parsear el archivo de stock", "error")
                self._update_actualizar_stock_status("Sin datos", warning())
        except Exception as ex:
            import traceback; traceback.print_exc()
            self._schedule_status(f"Error stock archivo: {ex}", "error")
            self._update_actualizar_stock_status(f"Error: {ex}", warning())

    def _apply_stock_data(self, stock: dict):
        self._merge_stock_to_catalogo(stock)
        _, _, stats = depurar_por_capas(stock, self.catalogo.productos)
        self._update_actualizar_stock_status(
            f"{stats['activos']}/{stats['total_erp']} activos", accent())
        self.app_state.lista_activa = None
        self._finalize_display(
            status_msg=f"Stock: {stats['activos']}/{stats['total_erp']} activos mergeados",
            status_level="success",
            switch_to_view=1,
        )

    def _on_category_assigned(self, sku: str, category: str):
        if category:
            self.maestro_comercial.asignar_categoria(sku, category)
        else:
            self.maestro_comercial.remover_categoria(sku)
        self.maestro_comercial.guardar()
        self._finalize_display(status_msg=f"Categor\u00eda asignada: {category}" if category else "Categor\u00eda removida", status_level="success")

    def _on_units_per_box_change(self, sku: str, ub: int):
        self.maestro_comercial.asignar_units_per_box(sku, ub)
        self.maestro_comercial.guardar()

    def _go_to_config(self):
        self.app_state.current_view = 2
        self.sidebar.nav_rail.selected_index = 2
        self._update_content()

    def _on_load_files_from_config(self, paths: dict):
        self.page.run_thread(self._load_from_paths, paths)

    def _load_from_paths(self, paths: dict):
        from src.core.parsers.plantilla_parser import parsear_plantilla_precios

        catalogo_path = paths.get("catalogo", "")
        plantilla_path = paths.get("plantilla", "")

        self.app_state.is_loading = True
        self.status_panel.set_loading(True, "Cargando archivos...")
        try:
            self.catalogo = CatalogoMaestro()

            if catalogo_path:
                filas = leer_xls_fallback(catalogo_path)
                if filas:
                    fuente = parsear_fuente(filas, catalogo_path)
                    if fuente.productos:
                        merge_result = self.source_manager.reemplazar_maestro(fuente)
                        for p in merge_result.productos:
                            self.catalogo.upsert(p)
                        self.status_panel.set_status(f"ERP: {len(fuente.productos)} productos", "success")

            self.status_panel.set_loading(True, "Descargando stock...")
            stock = download_stock()

            if stock:
                self._merge_stock_to_catalogo(stock)

            if plantilla_path:
                plant_productos, _, _ = parsear_plantilla_precios(plantilla_path)
                self._p2_skus.update(p.sku for p in plant_productos if p.sku)
                for p in plant_productos:
                    if p.sku in self.catalogo.productos:
                        existing = self.catalogo.productos[p.sku]
                        if not existing.units_per_box or existing.units_per_box == 1:
                            existing.units_per_box = p.units_per_box
                        if not existing.category:
                            existing.category = p.category
                        if not existing.description and p.description:
                            existing.description = p.description
                        if not existing.full_name and p.full_name:
                            existing.full_name = p.full_name
                        if not existing.ean13 and p.ean13:
                            existing.ean13 = p.ean13
                        if not existing.weight_kg and p.weight_kg:
                            existing.weight_kg = p.weight_kg
                        if not existing.line and p.line:
                            existing.line = p.line
                        if not existing.family and p.family:
                            existing.family = p.family
                        if not existing.group and p.group:
                            existing.group = p.group
                        if not existing.subcategory and p.subcategory:
                            existing.subcategory = p.subcategory
                        if not existing.currency and p.currency:
                            existing.currency = p.currency
                        if not existing.unit_of_measure or existing.unit_of_measure == 'UND':
                            if p.unit_of_measure and p.unit_of_measure != 'UND':
                                existing.unit_of_measure = p.unit_of_measure
                        if p.commercial_discounts:
                            existing.commercial_discounts = p.commercial_discounts
                        if p.additional_discounts:
                            existing.additional_discounts = p.additional_discounts
                        if p.rebate_override > 0:
                            existing.rebate_override = p.rebate_override
                        if p.special_override > 0:
                            existing.special_override = p.special_override
                        if p.price_type == 'FIJO' and p.fixed_price:
                            existing.price_type = 'FIJO'
                            existing.fixed_price = p.fixed_price

            self.app_state.lista_activa = None
            self.app_state.current_view = 2
            self.sidebar.nav_rail.selected_index = 2
            self._finalize_display(
                status_msg=f"Datos cargados: {len(self.catalogo.productos)} productos en catálogo",
                status_level="success",
            )
        except Exception as ex:
            import traceback; traceback.print_exc()
            self.status_panel.set_status(f"Error: {ex}", "error")
        finally:
            self.app_state.is_loading = False
            self.status_panel.set_loading(False)
