# game_launcher/gui/recent_favorites_tabs.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel,
    QSizePolicy, QSpacerItem, QHBoxLayout, QPushButton, QMenu,
    QStackedLayout # QActionGroup foi removido daqui
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon # E adicionado aqui
from PyQt6.QtCore import Qt, QPoint, QSize
from datetime import datetime
from gui.game_details_dialog import GameDetailsDialog
from gui.animated_card import AnimatedGameCard 
from gui.list_item_widget import GameListItemWidget

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
            date_label.setFixedWidth(140)
            hbox.addWidget(date_label)
            spacer = QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            hbox.addItem(spacer)
            play_btn = QPushButton("Detalhes")
            play_btn.clicked.connect(lambda _, g=game: self._show_game_details(g))
            hbox.addWidget(play_btn)
            container = QWidget()
            container.setLayout(hbox)
            recent_games_layout.addWidget(container)

        recent_games_layout.addStretch()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(recent_games_container)
        self.recent_layout.addWidget(scroll_area)

    def _show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog.exec()