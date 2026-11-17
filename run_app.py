#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cartela - Launcher Principal da Aplicação
Inicia o CartelaApp configurando caminhos para src, data e recursos.
"""

import sys
import os
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_FILES = os.path.join(ROOT, "app_files")
SRC_DIR = os.path.join(APP_FILES, "src")
CSHARP_UI_EXE = os.path.join(ROOT, "CartelaUI.exe")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

if __name__ == "__main__":
    if os.name == "nt" and "--tkinter" not in sys.argv and os.path.exists(CSHARP_UI_EXE):
        subprocess.Popen([CSHARP_UI_EXE], cwd=ROOT)
    else:
        try:
            from app.gui import CartelaApp
        except ImportError:
            from src.app.gui import CartelaApp
        app = CartelaApp()
        app.mainloop()
