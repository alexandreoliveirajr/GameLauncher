# game_launcher/gui/main_window.py

import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout,
    QLineEdit, QApplication,
    QMessageBox,
    QLabel
)
from PyQt5.QtCore import Qt, QTimer

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
        self.setWindowTitle("Launcher de Jogos")
        
        # --- FOLHA DE ESTILOS ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QLineEdit#search_input {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 5px 12px;
                color: white;
                font-size: 14px;
                selection-background-color: #66b3ff;
                selection-color: white;
            }
            QLineEdit#search_input::placeholder {
                color: #888;
            }
            QLineEdit#search_input:focus {
                border: 1px solid #66b3ff;
                background-color: #333;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #1e1e1e;
                border-top: none;
            }
            QTabBar::tab {
                background: #2c2c2c;
                color: white;
                padding: 12px 30px;
                margin: 0px 1px;
                border: 1px solid #3a3a3a;
                border-bottom: none; 
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #444;
                border-color: #555;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #555;
            }
            QTabBar::scroller {
                width: 60px;
            }
            QTabWidget::tab-bar {
                alignment: left;
                border-bottom: 1px solid #444;
            }

            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 14px;
                margin: 15px 0 15px 0;
                border-radius: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a5a5a;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #6a6a6a;
            }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 15px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

                        QMenu {
                background-color: #2a2d30;
                color: white;
                border: 1px solid #444;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 20px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 5px 0px;
            }

        """)

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
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("search_input")
        self.search_input.setPlaceholderText("🔍 Buscar jogos...")
        self.search_input.setFixedWidth(350)
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self._filter_library)

        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 10, 0) 
        search_layout.addWidget(self.search_input)
        
        self.tabs.setCornerWidget(search_container, Qt.TopRightCorner)

        self.library_tab_widget = LibraryTab(self.game_manager, self.game_launcher, self)
        self.profile_tab_widget = ProfileTab(self.profile_manager, self.game_manager, self)
        self.favorites_tab_widget = FavoritesTab(self.game_manager, self.game_launcher, self)
        self.recent_tab_widget = RecentTab(self.game_manager, self.game_launcher, self)
        self.add_game_tab_widget = AddGameTab(self.game_manager, self)
        self.import_tab_widget = ImportTab(self.game_manager, self)

        self.tabs.addTab(self.library_tab_widget, "Biblioteca")
        self.tabs.addTab(self.profile_tab_widget, "Perfil")
        self.tabs.addTab(self.favorites_tab_widget, "Favoritos")
        self.tabs.addTab(self.recent_tab_widget, "Jogos Recentes")
        self.tabs.addTab(self.add_game_tab_widget, "Adicionar Jogo")
        self.tabs.addTab(self.import_tab_widget, "Importar Jogos")

        main_layout.addWidget(self.tabs)
        
        self.tabs.currentChanged.connect(self._handle_tab_change)
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
                
                print(f"'{game['name']}' (PID: {pid}) foi fechado. Tempo jogado: {seconds_played}s.")
                
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
        print("Atualizando todas as abas...")
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

    def show_message_box(self, title, message, icon_type="info", buttons=QMessageBox.Ok):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if icon_type == "info":
            msg_box.setIcon(QMessageBox.Information)
        elif icon_type == "warning":
            msg_box.setIcon(QMessageBox.Warning)
        elif icon_type == "question":
            msg_box.setIcon(QMessageBox.Question)
        elif icon_type == "critical":
            msg_box.setIcon(QMessageBox.Critical)

        msg_box.setStandardButtons(buttons)
        msg_box.setStyleSheet("background-color: #2c2c2c; color: white; QPushButton { background-color: #444; color: white; }")
        return msg_box.exec_()
