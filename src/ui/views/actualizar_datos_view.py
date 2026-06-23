import flet as ft
from src.ui.views.base_view import BaseView
from src.ui.theme import rgba, F_SMALL, safe_page


class ActualizarDatosView(BaseView):
    def __init__(self, colors: dict, state=None, app=None):
        super().__init__(colors)
        self.state = state
        self.app = app
        self._built = False

    def build(self) -> ft.Control:
        if not self._built:
            self._build_controls()
        self._sync_controls()
        self._built = True
        return self._root

    def _build_controls(self):
        load_section = self._build_load_section()
        pending_section = self._build_pending_section()
        summary_section = self._build_summary_section()

        self._root = ft.Column([
            ft.Text("Actualizar Datos", size=18, weight=ft.FontWeight.W_800, color=self.colors["text_primary"]),
            ft.Divider(height=1, color="white12"),
            ft.Container(height=8),
            ft.Row([
                ft.Container(content=load_section, expand=1),
                ft.Container(width=16),
                ft.Container(content=summary_section, expand=1),
            ], expand=1),
            ft.Container(height=8),
            pending_section,
        ], spacing=0, expand=True)

    def _build_load_section(self) -> ft.Control:
        self._load_buttons = {}
        files = [
            ("catalogo", "Catálogo ERP (.xls)", ft.Icons.CLOUD_DOWNLOAD, self.colors["accent"]),
            ("categorias", "Categorías (.xlsx)", ft.Icons.CATEGORY, self.colors["warning"]),
            ("descuentos", "Descuentos (.xlsx)", ft.Icons.DISCOUNT, self.colors["warning"]),
            ("precios_fijos", "Precios Fijos (.xlsx)", ft.Icons.ATTACH_MONEY, self.colors["warning"]),
            ("traductor", "Traductor SKU (.xlsx)", ft.Icons.TRANSLATE, self.colors["warning"]),
            ("stock", "Stock Desde Archivo", ft.Icons.WAREHOUSE, self.colors["warning"]),
        ]
        cards = []
        for key, label, icon, color in files:
            btn = ft.OutlinedButton(
                label,
                icon=icon,
                height=32,
                style=ft.ButtonStyle(
                    padding=ft.Padding(8, 0, 8, 0),
                    text_style=ft.TextStyle(size=F_SMALL),
                    side=ft.BorderSide(1, "white24"),
                ),
                on_click=lambda e, k=key: self._on_load_file(k),
            )
            status = ft.Text("—", size=F_SMALL, color=self.colors["text_muted"])
            row = ft.Row([
                btn,
                ft.Container(width=8),
                status,
            ], vertical_alignment="center")
            card = ft.Container(
                content=row,
                padding=6,
                border=ft.Border.all(1, "white12"),
                border_radius=6,
            )
            self._load_buttons[key] = {"btn": btn, "status": status, "card": card}
            cards.append(card)

        stock_btn = ft.OutlinedButton(
            "Descargar Stock AppWeb",
            icon=ft.Icons.WIFI_FIND,
            height=32,
            style=ft.ButtonStyle(
                padding=ft.Padding(8, 0, 8, 0),
                text_style=ft.TextStyle(size=F_SMALL),
                side=ft.BorderSide(1, "white24"),
            ),
            on_click=lambda _: self._on_download_stock(),
        )
        self._stock_dl_status = ft.Text("—", size=F_SMALL, color=self.colors["text_muted"])
        stock_dl_row = ft.Container(
            content=ft.Row([stock_btn, ft.Container(width=8), self._stock_dl_status], vertical_alignment="center"),
            padding=6, border=ft.Border.all(1, "white12"), border_radius=6,
        )
        cards.append(stock_dl_row)

        recarga_btn = ft.FilledButton(
            "Recarga Completa ERP",
            icon=ft.Icons.REFRESH,
            height=36,
            on_click=lambda _: self._on_full_reload(),
        )
        return ft.Column([
            ft.Text("Carga de Datos", size=14, weight=ft.FontWeight.W_700, color=self.colors["accent"]),
            ft.Container(height=8),
            *cards,
            ft.Container(height=12),
            recarga_btn,
        ], spacing=6, scroll=ft.ScrollMode.AUTO)

    def _build_pending_section(self) -> ft.Control:
        self._pending_list = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO)
        self._pending_count = ft.Text("0", size=18, weight=ft.FontWeight.W_800, color=self.colors["warning"])
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Alertas y Pendientes", size=14, weight=ft.FontWeight.W_700, color=self.colors["warning"]),
                    ft.Container(expand=True),
                    self._pending_count,
                    ft.Text(" pendientes", size=F_SMALL, color=self.colors["text_muted"]),
                ], vertical_alignment="center"),
                self._pending_list,
            ]),
            padding=10,
            border=ft.Border.all(1, "white12"),
            border_radius=8,
            height=200,
        )

    def _build_summary_section(self) -> ft.Control:
        self._summary_labels = {}
        items = [
            ("total", "Total SKUs"),
            ("categorizados", "Con Categoría"),
            ("sin_categoria", "Sin Categoría"),
            ("con_stock", "Con Stock"),
            ("con_precio", "Con Precio"),
            ("divergentes", "Precios Divergentes"),
        ]
        rows = []
        for key, label in items:
            val = ft.Text("0", size=F_SMALL, color=self.colors["text_primary"], weight=ft.FontWeight.W_600)
            row = ft.Row([
                ft.Text(label, size=F_SMALL, color=self.colors["text_muted"], expand=True),
                val,
            ], spacing=4)
            rows.append(row)
            self._summary_labels[key] = val
        return ft.Column([
            ft.Text("Resumen", size=14, weight=ft.FontWeight.W_700, color=self.colors["accent"]),
            *rows,
        ], spacing=4)

    def _sync_controls(self):
        productos = self.state.productos if self.state else []
        catalogo = self.app.catalogo.productos if self.app else {}

        total = len(catalogo)
        categorizados = sum(1 for p in productos if p.category) if productos else 0
        sin_categoria = total - categorizados
        con_stock = sum(1 for p in productos if p.stock > 0) if productos else 0
        con_precio = sum(1 for p in productos if p.list_price > 0) if productos else 0
        divergentes = sum(1 for p in productos if getattr(p, "precio_divergente", False)) if productos else 0

        if hasattr(self, '_summary_labels'):
            self._summary_labels["total"].value = str(total)
            self._summary_labels["categorizados"].value = str(categorizados)
            self._summary_labels["sin_categoria"].value = str(sin_categoria)
            self._summary_labels["con_stock"].value = str(con_stock)
            self._summary_labels["con_precio"].value = str(con_precio)
            self._summary_labels["divergentes"].value = str(divergentes)

        self._build_pending(productos)

    def _build_pending(self, productos):
        pendientes = []
        if productos:
            sin = [p for p in productos if not p.category]
            if sin:
                pendientes.append(f"{len(sin)} SKU sin categoría asignada")
            sin_precio = [p for p in productos if p.list_price <= 0 and p.category]
            if sin_precio:
                pendientes.append(f"{len(sin_precio)} SKU sin precio de lista")
            sin_dto = [p for p in productos if p.category and not p.commercial_discounts and not (
                p._dc_ref and p._dc_ref.discounts
            )]
            if sin_dto:
                pendientes.append(f"{len(sin_dto)} SKU sin descuentos comerciales")
            divergentes_skus = [p for p in productos if getattr(p, "precio_divergente", False)]
            if divergentes_skus:
                pendientes.append(f"{len(divergentes_skus)} SKU con precios divergentes")

        if hasattr(self, '_pending_count'):
            self._pending_count.value = str(len(pendientes))
            if safe_page(self._pending_count):
                self._pending_count.update()

        if hasattr(self, '_pending_list'):
            self._pending_list.controls.clear()
            if pendientes:
                for p in pendientes:
                    self._pending_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Container(width=6, height=6, border_radius=3, bgcolor=self.colors["warning"]),
                                ft.Text(p, size=F_SMALL, color=self.colors["text_primary"]),
                            ], spacing=4, vertical_alignment="center"),
                            padding=ft.Padding(4, 2, 4, 2),
                        )
                    )
            else:
                self._pending_list.controls.append(
                    ft.Text("Sin pendientes", size=F_SMALL, color=self.colors["text_muted"])
                )
            if safe_page(self._pending_list):
                self._pending_list.update()

    def _on_load_file(self, key: str):
        if not self.app or not safe_page(self._root):
            return
        import tkinter as tk
        from tkinter import filedialog
        import gc
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.update()

        exts_map = {
            "catalogo": [("Archivos Excel", "*.xls *.xlsx"), ("Todos", "*.*")],
            "categorias": [("Excel", "*.xlsx"), ("Todos", "*.*")],
            "descuentos": [("Excel", "*.xlsx"), ("Todos", "*.*")],
            "precios_fijos": [("Excel", "*.xlsx"), ("Todos", "*.*")],
            "traductor": [("Excel", "*.xlsx"), ("Todos", "*.*")],
            "stock": [("Excel", "*.xls *.xlsx"), ("Todos", "*.*")],
        }
        try:
            path = filedialog.askopenfilename(
                title=f"Seleccionar {key}",
                filetypes=exts_map.get(key, [("Todos", "*.*")]),
            )
        finally:
            root.destroy()
            root = None
            gc.collect()
        if not path:
            return

        self._load_buttons[key]["status"].value = "Cargando..."
        self._load_buttons[key]["status"].update()

        handlers = {
            "catalogo": self.app._procesar_catalogo,
            "categorias": self.app._procesar_categorias,
            "descuentos": self.app._procesar_descuentos,
            "precios_fijos": self.app._procesar_precios_fijos,
            "traductor": self.app._procesar_traductor,
            "stock": self.app._procesar_stock_file,
        }
        handler = handlers.get(key)
        if handler:
            self.app.page.run_thread(handler, path)

    def _on_download_stock(self):
        if not self.app:
            return
        self._stock_dl_status.value = "Descargando..."
        self._stock_dl_status.update()
        self.app.page.run_thread(self.app._download_stock_thread)

    def _on_full_reload(self):
        if not self.app:
            return
        self.app.status_panel.set_loading(True, "Recarga completa del ERP...")
        self.app.page.run_thread(self.app._try_auto_load)

    def set_file_status(self, key: str, msg: str, color=None):
        if not hasattr(self, '_load_buttons'):
            return
        if key in self._load_buttons:
            self._load_buttons[key]["status"].value = msg
            if color:
                self._load_buttons[key]["status"].color = color
            self._load_buttons[key]["status"].update()

    def set_stock_status(self, msg: str, color=None):
        if hasattr(self, '_stock_dl_status'):
            self._stock_dl_status.value = msg
            if color:
                self._stock_dl_status.color = color
            self._stock_dl_status.update()
