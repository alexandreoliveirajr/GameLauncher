# game_launcher/gui/main_window.py

import sys
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QApplication, QMessageBox, QLabel,
    QPushButton, QFrame, QStackedWidget  # Adicionamos QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtGui import QIcon, QAction, QActionGroup
from PyQt6.QtCore import Qt, QTimer, QSize

from core.game_manager import GameManager
from core.game_launcher import GameLauncher
from core.profile_manager import ProfileManager
from core.settings_manager import SettingsManager

from gui.add_game_tab import AddGameTab
from gui.library_tab import LibraryTab
from gui.recent_favorites_tabs import FavoritesTab, RecentTab
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

        top_nav_bar_layout.addWidget(self.view_options_btn)

        top_nav_bar_layout.addStretch()

        # Campo de Busca
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍 Buscar na Biblioteca...")
        self.search_input.setFixedWidth(350)
        self.search_input.textChanged.connect(self.refresh_views)
        top_nav_bar_layout.addWidget(self.search_input)

        # Botão "Add Games"
        self.add_games_btn = QPushButton(" Add Games")
        self.add_games_btn.setObjectName("AddGamesButton")
        self.add_games_btn.setIcon(QIcon("assets/icons/plus-square.svg"))
        self.add_games_btn.setIconSize(QSize(16,16))
        top_nav_bar_layout.addWidget(self.add_games_btn)


        content_layout.addWidget(top_nav_bar) # Adiciona a barra de navegação ao layout
        # --- FIM DO BLOCO NOVO ---
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("MainContent")
        content_layout.addWidget(self.stacked_widget)

        self.library_tab_widget = LibraryTab(self.game_manager, self.game_launcher, self)
        self.profile_tab_widget = ProfileTab(self.profile_manager, self.game_manager, self)
        self.favorites_tab_widget = FavoritesTab(self.game_manager, self.game_launcher, self)
        self.recent_tab_widget = RecentTab(self.game_manager, self.game_launcher, self)
        self.add_game_tab_widget = AddGameTab(self.game_manager, self)
        self.import_tab_widget = ImportTab(self.game_manager, self)
        
        self.stacked_widget.addWidget(self.library_tab_widget)
        self.stacked_widget.addWidget(self.profile_tab_widget)
        self.stacked_widget.addWidget(self.favorites_tab_widget)
        self.stacked_widget.addWidget(self.recent_tab_widget)
        self.stacked_widget.addWidget(self.add_game_tab_widget)
        self.stacked_widget.addWidget(self.import_tab_widget)
        self.view_options_btn.clicked.connect(self.library_tab_widget.show_options_menu)

        btn_library.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.library_tab_widget))
        btn_profile.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.profile_tab_widget))
        btn_favorites.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.favorites_tab_widget))
        btn_recent.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.recent_tab_widget))
        btn_add_game.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.add_game_tab_widget))
        btn_import.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.import_tab_widget))

        # Agora, quando refresh_views for chamado, self.search_input já existe!
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

    def refresh_views(self):
        logging.info("Atualizando todas as visualizações (Biblioteca, Favoritos, etc.)...")
        search_term = self.search_input.text()

        # --- Lógica da BIBLIOTECA (permanece a mesma) ---
        lib_tag = self.library_tab_widget.current_tag
        lib_sort = self.library_tab_widget.current_sort
        filtered_and_sorted_games = self.game_manager.get_filtered_games(
            search_term, tag=lib_tag, sort_by=lib_sort
        )
        self.library_tab_widget.populate_games(filtered_and_sorted_games)

        # --- LÓGICA ATUALIZADA PARA FAVORITOS ---
        fav_sort = self.favorites_tab_widget.current_sort
        favorite_games = self.game_manager.get_favorite_games()

        # Aplica busca aos favoritos
        if search_term:
            search_lower = search_term.lower()
            favorite_games = [g for g in favorite_games if search_lower in g['name'].lower()]
        
        # Aplica ordenação aos favoritos
        if fav_sort == "Mais Jogado":
            favorite_games.sort(key=lambda g: g.get('total_playtime', 0), reverse=True)
        elif fav_sort == "Jogado Recentemente":
            for g in favorite_games:
                if isinstance(g.get("recent_play_time"), str):
                    try: g["recent_play_time"] = datetime.fromisoformat(g["recent_play_time"])
                    except: g["recent_play_time"] = None
            favorite_games.sort(key=lambda g: g.get('recent_play_time') or datetime.min, reverse=True)
        # "Nome (A-Z)" já é o padrão do get_favorite_games, mas podemos garantir
        else: 
             favorite_games.sort(key=lambda g: g['name'].lower())
        
        # O método populate_favorites agora sabe qual view (grade/lista) usar
        self.favorites_tab_widget.populate_favorites(favorite_games)
        
        # --- Resto da atualização (permanece o mesmo) ---
        self.recent_tab_widget.populate_recent_games(self.game_manager.get_recent_games())
        self.profile_tab_widget.load_profile_data()

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
