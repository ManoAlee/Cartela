#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cartela - Launcher Principal da Aplicação
Inicia o CartelaApp configurando caminhos para src, data e recursos.
"""

import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_FILES = os.path.join(ROOT, "app_files")
SRC_DIR = os.path.join(APP_FILES, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from app.gui import CartelaApp
except ImportError:
    from src.app.gui import CartelaApp

if __name__ == "__main__":
    app = CartelaApp()
    app.mainloop()
