# gui/library_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel,
    QSizePolicy, QSpacerItem, QHBoxLayout, QPushButton, QMenu,
    QStackedLayout # QActionGroup foi removido daqui
)
from PyQt6.QtGui import QAction, QActionGroup, QIcon # E adicionado aqui
from PyQt6.QtCore import Qt, QPoint, QSize
from gui.game_details_dialog import GameDetailsDialog
from gui.animated_card import AnimatedGameCard
from gui.list_item_widget import GameListItemWidget # Nosso card para a lista

class LibraryTab(QWidget):
    def __init__(self, game_manager, game_launcher, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref

        self.current_tag = "Todas"
        self.current_sort = "Nome (A-Z)"
        self.current_view = "Grade"

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)

        # Toolbar com o botão de opções
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 10)
        toolbar.addStretch()

        self.options_btn = QPushButton() # Deixe o texto vazio
        self.options_btn.setIcon(QIcon("assets/icons/sliders.svg"))
        self.options_btn.setIconSize(QSize(20, 20)) # Ajuste o tamanho do ícone
        self.options_btn.setFixedSize(40, 40)
        self.options_btn.clicked.connect(self.show_options_menu)
        self.options_btn.setToolTip("Exibir opções de visualização e ordenação")
        toolbar.addWidget(self.options_btn)
        main_layout.addLayout(toolbar)

        self.stacked_layout = QStackedLayout()

        # View de Grade
        self.grid_scroll_area = self._create_scroll_area()
        self.grid_container = self.grid_scroll_area.widget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(25)
        self.stacked_layout.addWidget(self.grid_scroll_area)

        # View de Lista
        self.list_scroll_area = self._create_scroll_area()
        self.list_container = self.list_scroll_area.widget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stacked_layout.addWidget(self.list_scroll_area)

        main_layout.addLayout(self.stacked_layout)

    def _create_scroll_area(self):
        """Função auxiliar para criar uma QScrollArea padronizada."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        scroll_area.setWidget(container)
        
        return scroll_area

    def populate_games(self, games_list):
        if self.current_view == "Grade":
            self.stacked_layout.setCurrentWidget(self.grid_scroll_area)
            self._populate_grid_view(games_list)
        else: # "Lista"
            self.stacked_layout.setCurrentWidget(self.list_scroll_area)
            self._populate_list_view(games_list)

    def _clear_layout(self, layout):
        """Limpa todos os widgets de um layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _populate_grid_view(self, games_list, columns=6):
        self._clear_layout(self.grid_layout)
        if not games_list:
            no_games_label = QLabel("Nenhum jogo encontrado.")
            no_games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(no_games_label, 0, 0, 1, columns)
            return

        for idx, game in enumerate(games_list):
            card = AnimatedGameCard(game, card_size=(200, 220))
            card.clicked.connect(lambda checked=False, g=game: self._show_game_details(g))
            row, col = idx // columns, idx % columns
            self.grid_layout.addWidget(card, row, col)
        
        self.grid_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), len(games_list) // columns + 1, 0)

    def _populate_list_view(self, games_list):
        self._clear_layout(self.list_layout)
        if not games_list:
            no_games_label = QLabel("Nenhum jogo encontrado.")
            no_games_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_layout.addWidget(no_games_label)
            return

        for game in games_list:
            item_widget = GameListItemWidget(game)
            item_widget.details_clicked.connect(lambda g=game: self._show_game_details(g))
            item_widget.play_clicked.connect(lambda g=game: self._launch_game_from_list(g))
            self.list_layout.addWidget(item_widget)
        
        self.list_layout.addStretch()

    def show_options_menu(self):
        # Este método já deve estar correto da sua implementação anterior
        menu = QMenu(self)
        sort_menu = menu.addMenu("Ordenar por")
        sort_group = QActionGroup(self)
        sort_options = ["Nome (A-Z)", "Mais Jogado", "Jogado Recentemente"]
        for option in sort_options:
            action = QAction(option, self, checkable=True)
            if option == self.current_sort: action.setChecked(True)
            action.triggered.connect(lambda checked, o=option: self.set_sort_option(o))
            sort_group.addAction(action); sort_menu.addAction(action)

        tags = ["Todas"] + self.game_manager.get_all_unique_tags()
        if len(tags) > 1:
            menu.addSeparator()
            tag_menu = menu.addMenu("Categoria")
            tag_group = QActionGroup(self)
            for tag in tags:
                action = QAction(tag, self, checkable=True)
                if tag == self.current_tag: action.setChecked(True)
                action.triggered.connect(lambda checked, t=tag: self.set_tag_filter(t))
                tag_group.addAction(action); tag_menu.addAction(action)

        menu.addSeparator()

        view_group = QActionGroup(self)
        grid_action = QAction("Grade", self, checkable=True)
        grid_action.setChecked(self.current_view == "Grade")
        grid_action.triggered.connect(lambda: self.set_view_mode("Grade"))
        view_group.addAction(grid_action); menu.addAction(grid_action)
        
        list_action = QAction("Lista", self, checkable=True)
        list_action.setChecked(self.current_view == "Lista")
        list_action.triggered.connect(lambda: self.set_view_mode("Lista"))
        view_group.addAction(list_action); menu.addAction(list_action)

        menu.exec(self.options_btn.mapToGlobal(QPoint(0, self.options_btn.height())))

    def set_sort_option(self, sort_by):
        self.current_sort = sort_by
        self.main_window_ref.refresh_views()
    
    def set_tag_filter(self, tag):
        self.current_tag = tag
        self.main_window_ref.refresh_views()
        
    def set_view_mode(self, view):
        self.current_view = view
        self.main_window_ref.refresh_views()

    def _show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog.exec()
        
    def _launch_game_from_list(self, game):
        paths = game.get("paths", [])
        if not paths:
            self.main_window_ref.show_message_box("Erro", "Este jogo não tem um executável configurado.", "warning")
            return
        
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self.main_window_ref)
        dialog._launch_game(paths[0]['path'])