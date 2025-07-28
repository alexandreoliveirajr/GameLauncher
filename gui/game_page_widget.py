# gui/game_page_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal, Qt

class GamePageWidget(QWidget):
    # Sinal que será emitido quando o usuário clicar em "Voltar"
    back_clicked = pyqtSignal()

    def __init__(self, game_data, parent=None):
        super().__init__(parent)
        self.setObjectName("GamePage")
        self.game_data = game_data
        
        self._setup_ui()

    def _setup_ui(self):
        # Layout principal da página
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Barra Superior com o botão "Voltar" ---
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(top_bar)
        
        back_button = QPushButton("← Voltar para a Biblioteca")
        back_button.setObjectName("BackButton")
        back_button.clicked.connect(self.back_clicked.emit) # Emite o sinal
        
        top_bar_layout.addWidget(back_button)
        top_bar_layout.addStretch()
        
        # --- Área de Conteúdo Principal ---
        # Usaremos um QFrame como container para podermos estilizar o fundo
        content_area = QFrame()
        content_area.setObjectName("ContentArea")
        
        # Por enquanto, apenas um texto de placeholder
        content_layout = QVBoxLayout(content_area)
        placeholder_label = QLabel(f"Página para o jogo: {self.game_data['name']}")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(placeholder_label)

        # Adiciona a barra e a área de conteúdo ao layout principal
        main_layout.addWidget(top_bar)
        main_layout.addWidget(content_area, 1) # O '1' faz a área de conteúdo esticar