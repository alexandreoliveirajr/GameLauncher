# game_launcher/gui/library_tab.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel, QSizePolicy, QSpacerItem
from PyQt5.QtCore import Qt
from gui.game_details_dialog import GameDetailsDialog
from gui.animated_card import AnimatedGameCard

class LibraryTab(QWidget):
    def __init__(self, game_manager, game_launcher, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 25, 20, 10)

        self.library_scroll = QScrollArea()
        self.library_scroll.setWidgetResizable(True)
        self.library_scroll.setStyleSheet("background-color: transparent; border: none;")

        self.library_container = QWidget()
        self.library_container.setStyleSheet("background-color: transparent;")
        
        self.library_grid = QGridLayout(self.library_container)
        self.library_grid.setSpacing(25)

        self.library_scroll.setWidget(self.library_container)
        layout.addWidget(self.library_scroll)
        self.setLayout(layout)

    def populate_games(self, games_list, columns=6, card_size=(200, 220)):
        while self.library_grid.count():
            item = self.library_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not games_list:
            no_games_label = QLabel("Nenhum jogo encontrado.")
            no_games_label.setStyleSheet("font-size: 18px; color: #aaa; margin-top: 50px;")
            no_games_label.setAlignment(Qt.AlignCenter) # Esta linha precisava da importação do Qt
            self.library_grid.addWidget(no_games_label, 0, 0, 1, columns)
            return

        for idx, game in enumerate(games_list):
            card = AnimatedGameCard(game, card_size)
            card.clicked.connect(lambda checked=False, g=game: self._show_game_details(g))
            
            row = idx // columns
            col = idx % columns
            self.library_grid.addWidget(card, row, col)
        
        num_rows = (len(games_list) + columns - 1) // columns
        self.library_grid.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), num_rows, 0)


    def _show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog.exec_()