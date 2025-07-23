import sys
import logging
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow # Importa a nossa nova classe MainWindow

def main():
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info("Iniciando a aplicação Game Launcher...")

    app = QApplication(sys.argv)
    launcher = MainWindow() # Agora instanciamos MainWindow
    launcher.show()

    logging.info("Aplicação iniciada com sucesso.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
