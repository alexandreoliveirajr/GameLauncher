# gui/igdb_search_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class IGDBSearchDialog(QDialog):
    def __init__(self, search_results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resultados da Busca no IGDB")
        self.setMinimumWidth(500)
        self.selected_game = None

        main_layout = QVBoxLayout(self)

        self.results_list = QListWidget()
        for game in search_results:
            # Mostra o nome e o ano de lançamento para facilitar a identificação
            release_year = game.get("release_date", "N/A").split('-')[0]
            list_text = f"{game['name']} ({release_year})"

            item = QListWidgetItem(list_text)
            # Guarda o dicionário completo do jogo no item da lista
            item.setData(Qt.ItemDataRole.UserRole, game)
            self.results_list.addItem(item)

        main_layout.addWidget(self.results_list)

        # Botões de OK e Cancelar
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Confirmar")
        ok_button.clicked.connect(self.on_accept)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        main_layout.addLayout(button_layout)

        self.results_list.itemDoubleClicked.connect(self.on_accept)

    def on_accept(self):
        current_item = self.results_list.currentItem()
        if current_item:
            # Pega o dicionário completo do jogo que guardamos
            self.selected_game = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def get_selected_game(self):
        return self.selected_game