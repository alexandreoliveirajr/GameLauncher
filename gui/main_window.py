# game_launcher/gui/main_window.py

import sys
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QApplication, QMessageBox, QLabel,
    QPushButton, QFrame, QStackedWidget, QMenu
)
from PyQt6.QtGui import QIcon, QAction, QActionGroup
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint

from core.game_manager import GameManager
from core.game_launcher import GameLauncher
from core.profile_manager import ProfileManager
from core.settings_manager import SettingsManager

from gui.game_display_widget import GameDisplayWidget
from gui.add_game_tab import AddGameTab
from gui.recent_favorites_tabs import RecentTab
from gui.game_details_dialog import GameDetailsDialog
from gui.profile_tab import ProfileTab
from gui.import_tab import ImportTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        self.setWindowTitle("Game Launcher")
        
        screen = QApplication.primaryScreen()
        rect = screen.availableGeometry()
        self.setGeometry(rect)
        self.showMaximized()

        self.game_manager = GameManager()
        self.game_launcher = GameLauncher(self.game_manager)
        self.profile_manager = ProfileManager()
        
        self.running_games = {}
        self.playtime_tracker = QTimer(self)
        self.playtime_tracker.setInterval(15000)
        self.playtime_tracker.timeout.connect(self._check_running_games)
        self.playtime_tracker.start()

        self.current_sort_by = "Nome (A-Z)"
        self.current_view_mode = "Grade"
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("LeftSidebar")
        self.sidebar.setFixedWidth(240)
        main_layout.addWidget(self.sidebar)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)

        logo_label = QLabel("GAME LAUNCHER")
        logo_label.setObjectName("LogoLabel")
        sidebar_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        icon_size = QSize(20, 20) # Tamanho padrão para os ícones

        btn_library = QPushButton(" Biblioteca")
        btn_library.setIcon(QIcon("assets/icons/home.svg"))
        btn_library.setIconSize(icon_size)

        btn_profile = QPushButton(" Perfil")
        btn_profile.setIcon(QIcon("assets/icons/user.svg"))
        btn_profile.setIconSize(icon_size)

        btn_favorites = QPushButton(" Favoritos")
        btn_favorites.setIcon(QIcon("assets/icons/star.svg"))
        btn_favorites.setIconSize(icon_size)

        btn_recent = QPushButton(" Recentes")
        btn_recent.setIcon(QIcon("assets/icons/clock.svg"))
        btn_recent.setIconSize(icon_size)

        btn_add_game = QPushButton(" Adicionar Jogo")
        btn_add_game.setIcon(QIcon("assets/icons/plus-square.svg"))
        btn_add_game.setIconSize(icon_size)

        btn_import = QPushButton(" Importar Jogos")
        btn_import.setIcon(QIcon("assets/icons/download.svg"))
        btn_import.setIconSize(icon_size)

        sidebar_layout.addWidget(btn_library)
        sidebar_layout.addWidget(btn_profile)
        sidebar_layout.addWidget(btn_favorites)
        sidebar_layout.addWidget(btn_recent)
        sidebar_layout.addWidget(btn_add_game)
        sidebar_layout.addWidget(btn_import)
        sidebar_layout.addStretch()

        self.content_area = QFrame()
        self.content_area.setObjectName("RightContentArea")
        main_layout.addWidget(self.content_area, 1)
        
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 10, 20, 20) # Adicionamos margens
        
        top_nav_bar = QFrame()
        top_nav_bar.setObjectName("TopNavBar")
        top_nav_bar_layout = QHBoxLayout(top_nav_bar)
        top_nav_bar_layout.setContentsMargins(0,0,0,0)

        # Botão de Opções de Exibição (movido para cá)
        self.view_options_btn = QPushButton()
        self.view_options_btn.setObjectName("ViewOptionsButton")
        self.view_options_btn.setIcon(QIcon("assets/icons/sliders.svg"))
        self.view_options_btn.setIconSize(QSize(20, 20))
        self.view_options_btn.setFixedSize(40, 40)
        self.view_options_btn.setToolTip("Opções de Exibição")

        self.view_options_btn.clicked.connect(self.show_options_menu)

        top_nav_bar_layout.addWidget(self.view_options_btn)

        top_nav_bar_layout.addStretch()

        # Campo de Busca
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍 Buscar na Biblioteca...")
        self.search_input.setFixedWidth(350)
        self.search_input.textChanged.connect(self.refresh_views)
        top_nav_bar_layout.addWidget(self.search_input)

        content_layout.addWidget(top_nav_bar) 
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("MainContent")
        content_layout.addWidget(self.stacked_widget)
        self.library_display = GameDisplayWidget(self)
        self.favorites_display = GameDisplayWidget(self)
        
        self.profile_tab_widget = ProfileTab(self.profile_manager, self.game_manager, self)
        
        self.recent_tab_widget = RecentTab(self.game_manager, self.game_launcher, self)
        self.add_game_tab_widget = AddGameTab(self.game_manager, self)
        self.import_tab_widget = ImportTab(self.game_manager, self)
        
        self.stacked_widget.addWidget(self.library_display)
        self.stacked_widget.addWidget(self.favorites_display)
        self.stacked_widget.addWidget(self.profile_tab_widget)
        self.stacked_widget.addWidget(self.recent_tab_widget)
        self.stacked_widget.addWidget(self.add_game_tab_widget)
        self.stacked_widget.addWidget(self.import_tab_widget)
        

        btn_library.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.library_display))
        btn_profile.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.profile_tab_widget))
        btn_favorites.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.favorites_display))
        btn_recent.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.recent_tab_widget))
        btn_add_game.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.add_game_tab_widget))
        btn_import.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.import_tab_widget))
        self.refresh_views()

    def start_tracking_game(self, process, game):
        if process and game:
            pid = process.pid
            if pid not in self.running_games:
                self.running_games[pid] = (process, game, datetime.now())
                print(f"Iniciando rastreamento para '{game['name']}' (PID: {pid})")

    def _check_running_games(self):
        if not self.running_games:
            return

        for pid in list(self.running_games.keys()):
            process, game, start_time = self.running_games[pid]
            
            if process.poll() is not None: 
                end_time = datetime.now()
                duration_seconds = (end_time - start_time).total_seconds()
                seconds_played = int(round(duration_seconds))
                
                logging.info(f"Processo do jogo '{game['name']}' (PID: {pid}) finalizado. Duração: {seconds_played}s.")
                
                if seconds_played > 0:
                    self.game_manager.add_playtime(game, seconds_played)
                    self.refresh_views()
                
                del self.running_games[pid]

    def _handle_tab_change(self, index):
        current_widget = self.tabs.widget(index)
        is_library = current_widget == self.library_tab_widget
        self.search_input.setEnabled(is_library)
        if not is_library:
            self.search_input.clear()
        
    def _filter_library(self, text):
        filtered_games = self.game_manager.get_filtered_games(text)
        self.library_tab_widget.populate_games(filtered_games)
        self.refresh_views()

    def set_sort_option(self, sort_by):
        """Atualiza a opção de ordenação e atualiza a tela."""
        self.current_sort_by = sort_by
        self.refresh_views()
    
    def set_view_mode(self, view_mode):
        self.current_view_mode = view_mode
        self.library_display.set_view_mode(view_mode)
        self.favorites_display.set_view_mode(view_mode)
        self.refresh_views()

        # Em gui/main_window.py, dentro da classe MainWindow

    def launch_game_from_list(self, game):
        """Inicia o primeiro executável de um jogo da lista."""
        paths = game.get("paths", [])
        if not paths:
            self.show_message_box("Erro", "Este jogo não tem um executável configurado.", "warning")
            return

        # Abre a janela de detalhes e já clica em "Jogar"
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self)
        dialog._launch_game(paths[0]['path'])

    def show_options_menu(self):
        menu = QMenu(self)
        
        # --- Menu de Ordenação ---
        sort_menu = menu.addMenu("Ordenar por")
        sort_group = QActionGroup(self)
        sort_options = ["Nome (A-Z)", "Mais Jogado", "Jogado Recentemente"]
        
        for option in sort_options:
            action = QAction(option, self)
            action.setCheckable(True)
            if option == self.current_sort_by:
                action.setChecked(True)
            action.triggered.connect(lambda checked, o=option: self.set_sort_option(o))
            sort_group.addAction(action)
            sort_menu.addAction(action)

        menu.addSeparator()

        # --- Menu de Visualização (Grade/Lista) ---
        view_group = QActionGroup(self)
        
        grid_action = QAction("Grade", self)
        grid_action.setCheckable(True)
        if self.current_view_mode == "Grade":
            grid_action.setChecked(True)
        grid_action.triggered.connect(lambda: self.set_view_mode("Grade"))
        view_group.addAction(grid_action)
        menu.addAction(grid_action)
        
        list_action = QAction("Lista", self)
        list_action.setCheckable(True)
        if self.current_view_mode == "Lista":
            list_action.setChecked(True)
        list_action.triggered.connect(lambda: self.set_view_mode("Lista"))
        view_group.addAction(list_action)
        menu.addAction(list_action)

        menu.exec(self.view_options_btn.mapToGlobal(QPoint(0, self.view_options_btn.height())))

    def show_game_details(self, game):
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self)
        dialog.exec()
        self.refresh_views()

    def refresh_views(self):
        logging.info("Atualizando todas as visualizações...")
        search_term = self.search_input.text()

        # 1. Popula a grade da Biblioteca Principal
        library_games = self.game_manager.get_filtered_games(search_term, sort_by=self.current_sort_by)
        self.library_display.populate_games(library_games)

        # 2. Popula a grade de Favoritos
        favorite_games = self.game_manager.get_favorite_games()
        # Filtra os favoritos se houver texto na busca
        if search_term:
            favorite_games = [g for g in favorite_games if search_term.lower() in g['name'].lower()]
        self.favorites_display.populate_games(favorite_games)

        # 3. Atualiza o resto
        self.recent_tab_widget.populate_recent_games(self.game_manager.get_recent_games())
        self.profile_tab_widget.load_profile_data()

    # Em gui/main_window.py, dentro da classe MainWindow

    def show_game_details(self, game):
        """Cria e exibe a janela de detalhes para um jogo específico."""
        dialog = GameDetailsDialog(game, self.game_manager, self.game_launcher, self)
        dialog.exec()
        # Atualizamos as views depois que o diálogo fecha, caso o usuário
        # tenha favoritado, editado ou deletado o jogo.
        self.refresh_views()

    def show_message_box(self, title, message, icon_type="info", buttons=QMessageBox.StandardButton.Ok):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if icon_type == "info":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif icon_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "question":
            msg_box.setIcon(QMessageBox.Icon.Question)
        elif icon_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)

        msg_box.setStandardButtons(buttons)
        return msg_box.exec()
