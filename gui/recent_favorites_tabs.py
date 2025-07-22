# game_launcher/gui/recent_favorites_tabs.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QScrollArea, QSizePolicy, QSpacerItem
from PyQt5.QtCore import Qt # <-- IMPORTAÇÃO CORRIGIDA
from gui.game_details_dialog import GameDetailsDialog
from gui.animated_card import AnimatedGameCard

class FavoritesTab(QWidget):
    def __init__(self, game_manager, game_launcher, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 25, 20, 10)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: transparent;")

        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(25)
        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def populate_favorites(self, favorite_games, columns=6, card_size=(200, 220)):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        if not favorite_games:
            no_games_label = QLabel("Nenhum jogo favorito encontrado.")
            no_games_label.setStyleSheet("font-size: 18px; color: #aaa; margin-top: 50px;")
            no_games_label.setAlignment(Qt.AlignCenter) # Esta linha precisava da importação
            self.grid_layout.addWidget(no_games_label, 0, 0, 1, columns)
            return

        for idx, game in enumerate(favorite_games):
            card = AnimatedGameCard(game, card_size)
            card.clicked.connect(lambda checked=False, g=game: self._show_game_details(g))
            row, col = idx // columns, idx % columns
            self.grid_layout.addWidget(card, row, col)
            
        num_rows = (len(favorite_games) + columns - 1) // columns
        self.grid_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), num_rows, 0)

    def _show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog.exec_()


# A aba de Recentes continua com o código original, pois não usa os cards animados
from datetime import datetime
from PyQt5.QtWidgets import QHBoxLayout, QPushButton

class RecentTab(QWidget):
    def __init__(self, game_manager, game_launcher, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref
        self._setup_ui()

    def _setup_ui(self):
        self.recent_layout = QVBoxLayout()
        self.recent_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.recent_layout)

    def populate_recent_games(self, recent_games):
        while self.recent_layout.count():
            child = self.recent_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        recent_games_container = QWidget()
        recent_games_layout = QVBoxLayout(recent_games_container)
        recent_games_layout.setContentsMargins(0, 0, 0, 0)
        recent_games_layout.setSpacing(5)

        for game in recent_games:
            hbox = QHBoxLayout()
            hbox.setContentsMargins(5, 2, 5, 2)
            hbox.setSpacing(15)
            name_label = QLabel(game["name"])
            name_label.setStyleSheet("color: white; font-weight: bold;")
            name_label.setFixedWidth(220)
            hbox.addWidget(name_label)
            play_time_obj = game.get("recent_play_time")
            dt_str = "Nunca jogado"
            if play_time_obj:
                try: 
                    dt_str = play_time_obj.strftime("%d/%m/%Y %H:%M")
                except Exception as e: 
                    dt_str = "Data inválida"
            date_label = QLabel(dt_str)
            date_label.setStyleSheet("color: #ccc;")
            date_label.setFixedWidth(140)
            hbox.addWidget(date_label)
            spacer = QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
            hbox.addItem(spacer)
            play_btn = QPushButton("Detalhes")
            play_btn.setStyleSheet("background-color: #444; color: white; padding: 5px 15px;")
            play_btn.clicked.connect(lambda _, g=game: self._show_game_details(g))
            hbox.addWidget(play_btn)
            container = QWidget()
            container.setLayout(hbox)
            recent_games_layout.addWidget(container)

        recent_games_layout.addStretch()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(recent_games_container)
        scroll_area.setStyleSheet("border: none; background-color: transparent;")
        self.recent_layout.addWidget(scroll_area)

    def _show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog.exec_()