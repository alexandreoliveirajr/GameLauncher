# gui/game_display_widget.py (VERSÃO FINAL COM ISOLAMENTO TOTAL)

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QSpacerItem, QSizePolicy, QStackedLayout, QGridLayout
from PyQt6.QtCore import Qt
from gui.animated_card import AnimatedGameCard
from gui.game_list_item_widget import GameListItemWidget

class GameDisplayWidget(QWidget):
    def __init__(self, main_window_ref):
        super().__init__()
        self.main_window_ref = main_window_ref
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_layout = QStackedLayout()

        # --- View de Grade ---
        grid_scroll_area = QScrollArea()
        grid_scroll_area.setWidgetResizable(True)
        grid_container = QWidget()
        grid_scroll_area.setWidget(grid_container)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # --- View de Lista ---
        list_scroll_area = QScrollArea()
        list_scroll_area.setWidgetResizable(True)
        list_container = QWidget()
        list_scroll_area.setWidget(list_container)
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.stacked_layout.addWidget(grid_scroll_area)
        self.stacked_layout.addWidget(list_scroll_area)
        
        main_layout.addLayout(self.stacked_layout)

    def set_view_mode(self, mode):
        if mode == "Grade":
            self.stacked_layout.setCurrentIndex(0)
        elif mode == "Lista":
            self.stacked_layout.setCurrentIndex(1)

    def populate_games(self, games_list):
        self._clear_layout(self.grid_layout)
        self._clear_layout(self.list_layout)
        
        if not games_list:
            no_games_label_grid = QLabel("Nenhum jogo encontrado.")
            no_games_label_grid.setObjectName("EmptyLibraryLabel")
            self.grid_layout.addWidget(no_games_label_grid, 0, 0, Qt.AlignmentFlag.AlignCenter)
            
            no_games_label_list = QLabel("Nenhum jogo encontrado.")
            no_games_label_list.setObjectName("EmptyLibraryLabel")
            self.list_layout.addWidget(no_games_label_list, 0, Qt.AlignmentFlag.AlignCenter)
            return

        columns = 6
        for idx, game in enumerate(games_list):
            # --- LÓGICA FINAL DA "CAIXA INVISÍVEL" ---
            card = AnimatedGameCard(game)
            card.clicked.connect(lambda g=game: self.main_window_ref.show_game_details(g))

            # 1. Cria a caixa estática com tamanho suficiente para a animação
            container = QWidget()
            # Adicionamos 10px de altura e largura para a animação "respirar"
            container.setFixedSize(card.width() + 10, card.height() + 10)
            
            # 2. Posiciona o card DENTRO da caixa, com espaço para animar
            card.setParent(container)
            card.move(5, 5)

            # 3. Adiciona a CAIXA à grade
            row, col = idx // columns, idx % columns
            self.grid_layout.addWidget(container, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            # --- FIM DA LÓGICA ---
            
            # Popula a Lista
            list_item = GameListItemWidget(game)
            list_item.details_clicked.connect(lambda g=game: self.main_window_ref.show_game_details(g))
            list_item.play_clicked.connect(lambda g=game: self.main_window_ref.launch_game_from_list(g))
            self.list_layout.addWidget(list_item)
        
        # O QGridLayout não precisa mais do Spacer, pois o alinhamento já cuida disso
        self.list_layout.addStretch()

    def _clear_layout(self, layout):
        if layout is None: return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self._clear_layout(sub_layout)