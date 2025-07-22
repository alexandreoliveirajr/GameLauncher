from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

class SearchTab(QWidget):
    # Sinal personalizado para emitir o texto de busca
    search_text_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50) # Espaçamento para o campo de busca
        layout.setAlignment(Qt.AlignCenter) # Centraliza o conteúdo

        search_label = QLabel("Pesquise seus jogos:")
        search_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        search_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o nome do jogo aqui...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                min-width: 400px; /* Garante uma largura mínima */
            }
            QLineEdit:focus {
                border: 1px solid #66b3ff; /* Borda azul ao focar */
            }
        """)
        self.search_input.setFixedHeight(40)
        self.search_input.setClearButtonEnabled(True) # Botão de limpar texto
        self.search_input.textChanged.connect(self.search_text_changed.emit) # Emite o sinal

        layout.addWidget(self.search_input, alignment=Qt.AlignCenter) # Centraliza o QLineEdit

        layout.addStretch() # Empurra o conteúdo para o centro/topo
        self.setLayout(layout)

    def get_search_text(self):
        return self.search_input.text()

    def clear_search(self):
        self.search_input.clear()