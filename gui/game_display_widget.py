# gui/game_display_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel, QSpacerItem, QSizePolicy, QStackedLayout
from PyQt6.QtCore import Qt
from gui.animated_card import AnimatedGameCard
from gui.game_list_item_widget import GameListItemWidget # <-- Nova importação

class GameDisplayWidget(QWidget): # <-- Classe renomeada
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window_ref = main_window_ref
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_layout = QStackedLayout() # <-- Usamos um StackedLayout

        # --- View de Grade (como antes) ---
        grid_scroll_area = QScrollArea()
        grid_scroll_area.setWidgetResizable(True)
        grid_container = QWidget()
        grid_scroll_area.setWidget(grid_container)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- View de Lista (NOVO) ---
        list_scroll_area = QScrollArea()
        list_scroll_area.setWidgetResizable(True)
        list_container = QWidget()
        list_scroll_area.setWidget(list_container)
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Adiciona as duas views ao StackedLayout
        self.stacked_layout.addWidget(grid_scroll_area)
        self.stacked_layout.addWidget(list_scroll_area)

        main_layout.addLayout(self.stacked_layout)

    def set_view_mode(self, mode):
        """Alterna entre 'Grade' e 'Lista'."""
        if mode == "Grade":
            self.stacked_layout.setCurrentIndex(0)
        elif mode == "Lista":
            self.stacked_layout.setCurrentIndex(1)

    def populate_games(self, games_list):
        self._clear_layout(self.grid_layout)
        self._clear_layout(self.list_layout)

        if not games_list:
            no_games_label_grid = QLabel("Nenhum jogo encontrado.")
            no_games_label_list = QLabel("Nenhum jogo encontrado.")
            self.grid_layout.addWidget(no_games_label_grid, 0, 0)
            self.list_layout.addWidget(no_games_label_list)
            return

        # --- LÓGICA CORRIGIDA ---
        # Um único loop para popular as duas visualizações ao mesmo tempo

        columns = 6
        for idx, game in enumerate(games_list):
            # Cria e configura o CARD para a GRADE
            card = AnimatedGameCard(game)
            card.clicked.connect(lambda g=game: self.main_window_ref.show_game_details(g))
            row, col = idx // columns, idx % columns
            self.grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)

            # Cria e configura o ITEM para a LISTA
            list_item = GameListItemWidget(game)
            list_item.details_clicked.connect(lambda g=game: self.main_window_ref.show_game_details(g))
            list_item.play_clicked.connect(lambda g=game: self.main_window_ref.launch_game_from_list(g))
            self.list_layout.addWidget(list_item)

        # Adiciona os espaçadores no final, fora do loop
        self.grid_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), 0, columns)
        self.list_layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()