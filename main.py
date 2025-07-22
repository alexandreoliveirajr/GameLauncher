import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow # Importa a nossa nova classe MainWindow

def main():
    app = QApplication(sys.argv)
    launcher = MainWindow() # Agora instanciamos MainWindow
    launcher.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
