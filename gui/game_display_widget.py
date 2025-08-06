# gui/game_display_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel, QSpacerItem, QSizePolicy, QStackedLayout, QGridLayout
# --- INÍCIO DA ALTERAÇÃO ---
# Importa o QTimer para a restauração da posição da barra de rolagem
from PyQt6.QtCore import Qt, QTimer
# --- FIM DA ALTERAÇÃO ---
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

        self.grid_scroll_area = QScrollArea()
        self.grid_scroll_area.setWidgetResizable(True)
        grid_container = QWidget()
        self.grid_scroll_area.setWidget(grid_container)
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(30)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.list_scroll_area = QScrollArea()
        self.list_scroll_area.setWidgetResizable(True)
        list_container = QWidget()
        self.list_scroll_area.setWidget(list_container)
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.stacked_layout.addWidget(self.grid_scroll_area)
        self.stacked_layout.addWidget(self.list_scroll_area)
        
        main_layout.addLayout(self.stacked_layout)

    def set_view_mode(self, mode):
        if mode == "Grade":
            self.stacked_layout.setCurrentIndex(0)
        elif mode == "Lista":
            self.stacked_layout.setCurrentIndex(1)

    def populate_games(self, games_list, scroll_pos=0):
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
            card = AnimatedGameCard(game)
            card.clicked.connect(lambda g=game: self.main_window_ref.show_game_details(g))

            container = QWidget()
            container.setFixedSize(card.width() + 10, card.height() + 10)
            
            card.setParent(container)
            card.move(5, 5)

            row, col = idx // columns, idx % columns
            self.grid_layout.addWidget(container, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            
            list_item = GameListItemWidget(game)
            list_item.details_clicked.connect(lambda g=game: self.main_window_ref.show_game_details(g))
            list_item.play_clicked.connect(lambda g=game: self.main_window_ref.launch_game_from_list(g))
            self.list_layout.addWidget(list_item)
        
        self.list_layout.addStretch()

        # --- INÍCIO DA ALTERAÇÃO ---
        # Se uma posição de rolagem foi passada, restaura-a usando um QTimer
        if scroll_pos > 0:
            # O QTimer.singleShot(0, ...) agenda a função para ser executada
            # assim que o loop de eventos principal estiver livre, garantindo
            # que a UI já tenha sido redesenhada.
            QTimer.singleShot(0, lambda: self.set_scroll_position(scroll_pos))
        # --- FIM DA ALTERAÇÃO ---


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

    def get_scroll_position(self):
        """Retorna a posição vertical atual da barra de rolagem da vista ativa."""
        if self.stacked_layout.currentIndex() == 0: # Grade
            return self.grid_scroll_area.verticalScrollBar().value()
        else: # Lista
            return self.list_scroll_area.verticalScrollBar().value()

    def set_scroll_position(self, position):
        """Define a posição vertical da barra de rolagem da vista ativa."""
        if self.stacked_layout.currentIndex() == 0: # Grade
            self.grid_scroll_area.verticalScrollBar().setValue(position)
        else: # Lista
            self.list_scroll_area.verticalScrollBar().setValue(position)
