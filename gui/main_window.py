# game_launcher/gui/main_window.py

import sys
import logging
import webbrowser
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
from core.folder_scanner import SteamScanner, LocalGameScanner

from gui.game_display_widget import GameDisplayWidget
from gui.game_page_widget import GamePageWidget
from gui.add_game_tab import AddGameTab
from gui.recent_favorites_tabs import RecentTab
from gui.profile_tab import ProfileTab
from gui.import_tab import ImportTab
from gui.settings_tab import SettingsTab

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.app = QApplication.instance()
        self.setWindowTitle("Game Launcher")
        
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())
        self.showMaximized()

        self.game_manager = GameManager()
        self.game_launcher = GameLauncher(self.game_manager)
        self.profile_manager = ProfileManager()
        self.settings_manager = SettingsManager()

        self.current_game_page = None
        self.last_view_widget = None
        self.running_games = {}
        self.last_scroll_position = 0
        # --- INÍCIO DA ADIÇÃO ---
        # 1. Adiciona uma "bandeira" para controlar a navegação
        self.is_navigating_back = False
        # --- FIM DA ADIÇÃO ---

        self.current_sort_by = self.settings_manager.get_setting("sort_by") or "Nome (A-Z)"
        self.current_view_mode = self.settings_manager.get_setting("view_mode") or "Grade"
        self.current_tag_filter = None
        self.current_status_filter = self.settings_manager.get_setting("status_filter") or "Todos"
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("LeftSidebar")
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)
        main_layout.addWidget(self.sidebar)
        
        self.content_area = QFrame()
        self.content_area.setObjectName("RightContentArea")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.addWidget(self.content_area, 1)

        self.top_nav_bar = QFrame()
        self.top_nav_bar.setObjectName("TopNavBar")
        self.top_nav_bar_layout = QHBoxLayout(self.top_nav_bar)
        self.top_nav_bar_layout.setContentsMargins(0,0,0,0)

        self.view_options_btn = QPushButton(icon=QIcon("assets/icons/sliders.svg"))
        self.view_options_btn.setObjectName("ViewOptionsButton")
        self.view_options_btn.setIconSize(QSize(20, 20))
        self.view_options_btn.setFixedSize(40, 40)
        self.view_options_btn.setToolTip("Opções de Exibição")
        self.top_nav_bar_layout.addWidget(self.view_options_btn)

        self.top_nav_bar_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍 Buscar na Biblioteca...")
        self.search_input.setFixedWidth(350)
        self.top_nav_bar_layout.addWidget(self.search_input)
        
        self.content_layout.addWidget(self.top_nav_bar)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("MainContent")
        self.content_layout.addWidget(self.stacked_widget)

        self.library_display = GameDisplayWidget(self)
        self.favorites_display = GameDisplayWidget(self)
        self.library_display.set_view_mode(self.current_view_mode)
        self.favorites_display.set_view_mode(self.current_view_mode)
        self.profile_tab_widget = ProfileTab(self.profile_manager, self.game_manager, self)
        self.recent_tab_widget = RecentTab(self.game_manager, self.game_launcher, self)
        self.add_game_tab_widget = AddGameTab(self.game_manager, self)
        self.import_tab_widget = ImportTab(self.game_manager, self)
        self.settings_tab_widget = SettingsTab(self.profile_manager, self)
        
        self.stacked_widget.addWidget(self.library_display)
        self.stacked_widget.addWidget(self.favorites_display)
        self.stacked_widget.addWidget(self.profile_tab_widget)
        self.stacked_widget.addWidget(self.recent_tab_widget)
        self.stacked_widget.addWidget(self.add_game_tab_widget)
        self.stacked_widget.addWidget(self.import_tab_widget)
        self.stacked_widget.addWidget(self.settings_tab_widget)

        logo_label = QLabel("GAME LAUNCHER"); logo_label.setObjectName("LogoLabel")
        sidebar_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        icon_size = QSize(20, 20)
        btn_library = QPushButton(" Biblioteca", icon=QIcon("assets/icons/home.svg")); btn_library.setIconSize(icon_size)
        btn_profile = QPushButton(" Perfil", icon=QIcon("assets/icons/user.svg")); btn_profile.setIconSize(icon_size)
        btn_favorites = QPushButton(" Favoritos", icon=QIcon("assets/icons/star.svg")); btn_favorites.setIconSize(icon_size)
        btn_recent = QPushButton(" Recentes", icon=QIcon("assets/icons/clock.svg")); btn_recent.setIconSize(icon_size)
        btn_add_game = QPushButton(" Adicionar Jogo", icon=QIcon("assets/icons/plus-square.svg")); btn_add_game.setIconSize(icon_size)
        btn_import = QPushButton(" Importar Jogos", icon=QIcon("assets/icons/download.svg")); btn_import.setIconSize(icon_size)

        sidebar_layout.addWidget(btn_library)
        sidebar_layout.addWidget(btn_profile)
        sidebar_layout.addWidget(btn_favorites)
        sidebar_layout.addWidget(btn_recent)
        sidebar_layout.addWidget(btn_add_game)
        sidebar_layout.addWidget(btn_import)
        sidebar_layout.addStretch()

        btn_settings = QPushButton(" Configurações", icon=QIcon("assets/icons/settings.svg")); btn_settings.setIconSize(icon_size)
        sidebar_layout.addWidget(btn_settings)

        self.playtime_tracker = QTimer(self)
        self.playtime_tracker.setInterval(15000)
        self.playtime_tracker.timeout.connect(self._check_running_games)
        self.playtime_tracker.start()
        
        self.search_input.textChanged.connect(self.refresh_views)
        self.view_options_btn.clicked.connect(self.show_options_menu)

        btn_library.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.library_display))
        btn_profile.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.profile_tab_widget))
        btn_favorites.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.favorites_display))
        btn_recent.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.recent_tab_widget))
        btn_add_game.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.add_game_tab_widget))
        btn_import.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.import_tab_widget))
        btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.settings_tab_widget))
        
        self.stacked_widget.currentChanged.connect(self._on_page_changed)

        self.refresh_views()
        self._on_page_changed(self.stacked_widget.currentIndex())

    def _on_page_changed(self, index):
        # --- INÍCIO DA ALTERAÇÃO ---
        # 2. Verifica a "bandeira" para evitar a atualização dupla
        if self.is_navigating_back:
            return
        # --- FIM DA ALTERAÇÃO ---

        current_widget = self.stacked_widget.widget(index)
        shows_top_bar = current_widget in [self.library_display, self.favorites_display]
        self.top_nav_bar.setVisible(shows_top_bar)
        is_full_bleed_page = (
            isinstance(current_widget, GamePageWidget) or
            current_widget == self.profile_tab_widget
        )
        if is_full_bleed_page:
            self.content_layout.setContentsMargins(0, 0, 0, 0)
        else:
            self.content_layout.setContentsMargins(50, 40, 50, 40)
        if shows_top_bar:
            self.refresh_views()

    def start_tracking_game(self, process, game):
        if process and game:
            pid = process.pid
            if pid not in self.running_games:
                self.running_games[pid] = (process, game, datetime.now())
                print(f"Iniciando rastreamento para '{game['name']}' (PID: {pid})")

    def _check_running_games(self):
        if not self.running_games: return
        for pid in list(self.running_games.keys()):
            process, game, start_time = self.running_games[pid]
            if process.poll() is not None: 
                end_time = datetime.now()
                duration_seconds = (end_time - start_time).total_seconds()
                seconds_played = int(round(duration_seconds))
                logging.info(f"Processo do jogo '{game['name']}' (PID: {pid}) finalizado. Duração: {seconds_played}s.")
                if seconds_played > 0:
                    self.game_manager.add_playtime(game['id'], seconds_played)
                    self.refresh_views()
                del self.running_games[pid]

    def set_sort_option(self, sort_by):
        self.current_sort_by = sort_by
        self.settings_manager.save_setting("sort_by", sort_by)
        self.refresh_views()
    
    def set_view_mode(self, view_mode):
        self.current_view_mode = view_mode
        self.settings_manager.save_setting("view_mode", view_mode)
        self.library_display.set_view_mode(view_mode)
        self.favorites_display.set_view_mode(view_mode)

    def set_tag_filter(self, tag):
        self.current_tag_filter = tag
        self.refresh_views()

    def set_status_filter(self, status):
        self.current_status_filter = status
        self.settings_manager.save_setting("status_filter", status)
        self.refresh_views()

    def launch_game_from_list(self, game):
        is_installed = game.get("status", "UNINSTALLED") == "INSTALLED"
        source = game.get("source")
        app_id = game.get("app_id")
        if not is_installed and source == 'steam' and app_id:
            install_path = f"steam://install/{app_id}"
            logging.info(f"Iniciando instalação do jogo da Steam via protocolo: {install_path}")
            webbrowser.open(install_path)
            self.show_message_box("Steam", "A instalação foi iniciada no cliente Steam.", "info")
            return
        paths = game.get("paths", [])
        if not paths:
            self.show_message_box("Erro", "Este jogo não tem um executável configurado.", "warning")
            return
        executable_path = paths[0]['path']
        if executable_path.startswith("steam://"):
            logging.info(f"Iniciando jogo da Steam via protocolo: {executable_path}")
            webbrowser.open(executable_path)
            self.game_manager.update_last_played(game['id'])
        else:
            result, data = self.game_launcher.launch_game(game, executable_path)
            if isinstance(result, str) and result == "error":
                self.show_message_box("Erro ao Iniciar", data, "warning")
            elif isinstance(result, str) and result == "running":
                self.show_message_box("Aviso", "Este jogo já está em execução.", "info")
            else:
                self.start_tracking_game(result, data)

    def show_options_menu(self):
        menu = QMenu(self)
        status_menu = menu.addMenu("Mostrar")
        status_group = QActionGroup(self)
        status_options = ["Todos", "Instalados"]
        for option in status_options:
            action = QAction(option, self, checkable=True)
            if option == self.current_status_filter:
                action.setChecked(True)
            action.triggered.connect(lambda checked, o=option: self.set_status_filter(o))
            status_group.addAction(action)
            status_menu.addAction(action)
        menu.addSeparator()
        sort_menu = menu.addMenu("Ordenar por")
        sort_group = QActionGroup(self)
        sort_options = ["Nome (A-Z)", "Mais Jogado", "Jogado Recentemente"]
        for option in sort_options:
            action = QAction(option, self, checkable=True)
            if option == self.current_sort_by: action.setChecked(True)
            action.triggered.connect(lambda checked, o=option: self.set_sort_option(o))
            sort_group.addAction(action)
            sort_menu.addAction(action)
        menu.addSeparator()
        tag_menu = menu.addMenu("Filtrar por Tag")
        tag_group = QActionGroup(self)
        all_tags_action = QAction("Todos", self, checkable=True)
        if self.current_tag_filter is None: all_tags_action.setChecked(True)
        all_tags_action.triggered.connect(lambda: self.set_tag_filter(None))
        tag_group.addAction(all_tags_action)
        tag_menu.addAction(all_tags_action)
        tag_menu.addSeparator()
        all_tags = self.game_manager.get_all_unique_tags()
        for tag_name in all_tags:
            tag_action = QAction(tag_name, self, checkable=True)
            if tag_name == self.current_tag_filter: tag_action.setChecked(True)
            tag_action.triggered.connect(lambda checked, t=tag_name: self.set_tag_filter(t))
            tag_group.addAction(tag_action)
            tag_menu.addAction(tag_action)
        menu.addSeparator()
        view_group = QActionGroup(self)
        grid_action = QAction("Grade", self, checkable=True)
        if self.current_view_mode == "Grade": grid_action.setChecked(True)
        grid_action.triggered.connect(lambda: self.set_view_mode("Grade"))
        view_group.addAction(grid_action)
        menu.addAction(grid_action)
        list_action = QAction("Lista", self, checkable=True)
        if self.current_view_mode == "Lista": list_action.setChecked(True)
        list_action.triggered.connect(lambda: self.set_view_mode("Lista"))
        view_group.addAction(list_action)
        menu.addAction(list_action)
        menu.exec(self.view_options_btn.mapToGlobal(QPoint(0, self.view_options_btn.height())))

    def show_game_details(self, game):
        if self.stacked_widget.currentWidget() in [self.library_display, self.favorites_display]:
            current_display = self.stacked_widget.currentWidget()
            self.last_scroll_position = current_display.get_scroll_position()
        
        if self.current_game_page: self.return_to_library_view()
        self.last_view_widget = self.stacked_widget.currentWidget()
        self.current_game_page = GamePageWidget(game, self.game_manager, self.game_launcher, self)
        self.current_game_page.back_clicked.connect(self.return_to_library_view)
        self.stacked_widget.addWidget(self.current_game_page)
        self.stacked_widget.setCurrentWidget(self.current_game_page)

    def refresh_views(self, restore_scroll=False):
        logging.info("Atualizando todas as visualizações...")
        search_term = self.search_input.text()
        library_games = self.game_manager.get_filtered_games(
            search_text=search_term, 
            tag=self.current_tag_filter, 
            sort_by=self.current_sort_by,
            status_filter=self.current_status_filter
        )
        
        scroll_pos = self.last_scroll_position if restore_scroll else 0
        self.library_display.populate_games(library_games, scroll_pos=scroll_pos)
        
        favorite_games = self.game_manager.get_favorite_games(status_filter=self.current_status_filter)
        if search_term:
            favorite_games = [g for g in favorite_games if search_term.lower() in g['name'].lower()]
        self.favorites_display.populate_games(favorite_games, scroll_pos=scroll_pos)
        
        self.recent_tab_widget.populate_recent_games(self.game_manager.get_recent_games())
        self.profile_tab_widget.load_profile_data()

    def show_message_box(self, title, message, icon_type="info", buttons=QMessageBox.StandardButton.Ok):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        if icon_type == "info": msg_box.setIcon(QMessageBox.Icon.Information)
        elif icon_type == "warning": msg_box.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "question": msg_box.setIcon(QMessageBox.Icon.Question)
        elif icon_type == "critical": msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setStandardButtons(buttons)
        return msg_box.exec()

    def return_to_library_view(self):
        # --- INÍCIO DA ALTERAÇÃO ---
        # 3. A lógica de restauração agora é mais limpa
        if self.last_view_widget:
            self.is_navigating_back = True
            self.stacked_widget.setCurrentWidget(self.last_view_widget)
            self.is_navigating_back = False

        if self.current_game_page:
            self.stacked_widget.removeWidget(self.current_game_page)
            self.current_game_page.deleteLater()
            self.current_game_page = None
        
        # A única chamada de refresh acontece aqui, com a flag correta
        self.refresh_views(restore_scroll=True)
        # --- FIM DA ALTERAÇÃO ---

    def show_loading_overlay(self, text="Carregando..."):
        if not hasattr(self, 'loading_label'):
            self.loading_label = QLabel(text, self)
            self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.loading_label.setStyleSheet("""
                background-color: rgba(0, 0, 0, 180); color: white;
                font-size: 24px; font-weight: bold; border-radius: 10px;
            """)
        self.loading_label.setText(text)
        if hasattr(self, 'centralWidget'):
             self.loading_label.setGeometry(self.centralWidget().rect())
        else:
             self.loading_label.setGeometry(self.rect())
        self.loading_label.raise_()
        self.loading_label.show()

    def hide_loading_overlay(self):
        if hasattr(self, 'loading_label'):
            self.loading_label.hide()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_label') and self.loading_label.isVisible():
            if hasattr(self, 'centralWidget'):
                 self.loading_label.setGeometry(self.centralWidget().rect())
            else:
                 self.loading_label.setGeometry(self.rect())
