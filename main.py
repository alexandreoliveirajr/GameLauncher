# main.py (VERSÃO FINAL DO PASSO 1)

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFileSystemWatcher

from gui.main_window import MainWindow
from core.database import initialize_database

# --- NOSSO NOVO SISTEMA DE TEMAS ---
THEME_COLORS = {
    # Placeholders e seus valores de cor
    "{background}": "#1e1e1e",
    "{background-darker}": "#111111",
    "{card}": "#2e2e2e",
    "{card-border}": "#3a3d40",
    "{text-primary}": "#ffffff",
    "{text-secondary}": "#cccccc",
    "{accent}": "#4a90e2",
    # Adicione outras cores aqui conforme necessário
}

def load_stylesheet(app):
    """Lê o arquivo QSS, substitui os placeholders de cor e o aplica."""
    try:
        with open("styles/main.qss", "r") as f:
            style_sheet = f.read()

        # Itera sobre o dicionário de cores e substitui os placeholders
        for placeholder, color in THEME_COLORS.items():
            style_sheet = style_sheet.replace(placeholder, color)
        
        app.setStyleSheet(style_sheet)
        logging.info("Folha de estilo QSS formatada e carregada com sucesso.")

    except FileNotFoundError:
        logging.warning("Arquivo de estilo 'styles/main.qss' não encontrado.")
    except Exception as e:
        logging.error(f"Erro ao carregar QSS: {e}")

def main():
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    initialize_database()

    logging.info("Iniciando a aplicação Game Launcher...")

    app = QApplication(sys.argv)
    
    load_stylesheet(app)

    # Monitor de arquivos para recarregamento automático
    # Ele agora só precisa observar um arquivo!
    watcher = QFileSystemWatcher(["styles/main.qss"])
    watcher.fileChanged.connect(lambda: load_stylesheet(app))

    launcher = MainWindow()
    launcher.show()

    logging.info("Aplicação iniciada com sucesso.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()