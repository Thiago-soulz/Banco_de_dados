"""
main.py

Ponto de entrada do CNC Transfer System
"""

import os
import sys
import logging
import customtkinter as ctk

# ==========================================================
# Adiciona a raiz do projeto ao PYTHONPATH
# ==========================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ==========================================================
# Imports do projeto
# ==========================================================

from ui.screens.main_window import MainWindow

# ==========================================================
# Log
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ==========================================================
# Tema
# ==========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ==========================================================
# Inicialização
# ==========================================================

def main():

    app = MainWindow()

    app.mainloop()


if __name__ == "__main__":
    main()