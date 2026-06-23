"""Abstract view base: every app view inherits from BaseView and implements build()."""

import flet as ft


class BaseView:
    def __init__(self, colors: dict):
        self.colors = colors

    def build(self) -> ft.Control:
        return ft.Container()
