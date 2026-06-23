#!/usr/bin/env python3
import flet as ft
from src.ui.main_app import G360ErpPriceList


def main(page: ft.Page):
    G360ErpPriceList(page)


if __name__ == "__main__":
    ft.run(main)
