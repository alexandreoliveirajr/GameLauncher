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


class FavoritesTab(QWidget):
    def __init__(self, game_manager, game_launcher, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref

        self.current_sort = "Nome (A-Z)"
        self.current_view = "Grade"

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 10)
        toolbar.addStretch()

        self.options_btn = QPushButton("⚙️")
        self.options_btn.setFixedSize(40, 40)
        self.options_btn.clicked.connect(self.show_options_menu)
        self.options_btn.setToolTip("Exibir opções de visualização e ordenação")
        toolbar.addWidget(self.options_btn)
        main_layout.addLayout(toolbar)

        self.stacked_layout = QStackedLayout()

        self.grid_scroll_area = self._create_scroll_area()
        self.grid_container = self.grid_scroll_area.widget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(25)
        self.stacked_layout.addWidget(self.grid_scroll_area)

        self.list_scroll_area = self._create_scroll_area()
        self.list_container = self.list_scroll_area.widget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stacked_layout.addWidget(self.list_scroll_area)

        main_layout.addLayout(self.stacked_layout)

    def populate_favorites(self, favorite_games):
        if self.current_view == "Grade":
            self.stacked_layout.setCurrentWidget(self.grid_scroll_area)
            self._populate_grid_view(favorite_games)
        else:
            self.stacked_layout.setCurrentWidget(self.list_scroll_area)
            self._populate_list_view(favorite_games)

    def show_options_menu(self):
        menu = QMenu(self)
        
        sort_menu = menu.addMenu("Ordenar por")
        sort_group = QActionGroup(self)
        sort_options = ["Nome (A-Z)", "Mais Jogado", "Jogado Recentemente"]
        for option in sort_options:
            action = QAction(option, self, checkable=True)
            if option == self.current_sort: action.setChecked(True)
            action.triggered.connect(lambda checked, o=option: self.set_sort_option(o))
            sort_group.addAction(action)
            sort_menu.addAction(action)
            
        menu.addSeparator()

        view_group = QActionGroup(self)
        grid_action = QAction("Grade", self, checkable=True)
        grid_action.setChecked(self.current_view == "Grade")
        grid_action.triggered.connect(lambda: self.set_view_mode("Grade"))
        view_group.addAction(grid_action)
        menu.addAction(grid_action)
        
        list_action = QAction("Lista", self, checkable=True)
        list_action.setChecked(self.current_view == "Lista")
        list_action.triggered.connect(lambda: self.set_view_mode("Lista"))
        view_group.addAction(list_action)
        menu.addAction(list_action)

        menu.exec(self.options_btn.mapToGlobal(QPoint(0, self.options_btn.height())))

    def set_sort_option(self, sort_by):
        self.current_sort = sort_by
        self.main_window_ref.refresh_views()
    
    def set_view_mode(self, view):
        self.current_view = view
        self.main_window_ref.refresh_views()
    
    def _create_scroll_area(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        scroll_area.setWidget(container)
        return scroll_area

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _populate_grid_view(self, games_list, columns=6):
        self._clear_layout(self.grid_layout)
        if not games_list:
            no_games_label = QLabel("Nenhum jogo favorito."); no_games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(no_games_label, 0, 0, 1, columns)
            return
        for idx, game in enumerate(games_list):
            card = AnimatedGameCard(game, card_size=(200, 220)); card.clicked.connect(lambda checked=False, g=game: self._show_game_details(g))
            row, col = idx // columns, idx % columns; self.grid_layout.addWidget(card, row, col)
        self.grid_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), (len(games_list) -1) // columns + 1, 0)

    def _populate_list_view(self, games_list):
        self._clear_layout(self.list_layout)
        if not games_list:
            no_games_label = QLabel("Nenhum jogo favorito."); no_games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(no_games_label)
            return
        for game in games_list:
            item_widget = GameListItemWidget(game); item_widget.details_clicked.connect(lambda g=game: self._show_game_details(g)); item_widget.play_clicked.connect(lambda g=game: self._launch_game_from_list(g))
            self.list_layout.addWidget(item_widget)
        self.list_layout.addStretch()

    def _show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog.exec()
        
    def _launch_game_from_list(self, game):
        paths = game.get("paths", [])
        if not paths: self.main_window_ref.show_message_box("Erro", "Este jogo não tem um executável configurado.", "warning"); return
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref); dialog._launch_game(paths[0]['path'])

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