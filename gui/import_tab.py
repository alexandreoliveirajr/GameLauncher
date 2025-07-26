# gui/import_tab.py

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QCheckBox, QLabel, QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt

from core.folder_scanner import FolderScanner
from core.settings_manager import SettingsManager
from core import steam_api

class ImportTab(QWidget):
    def __init__(self, game_manager, main_window_ref):
        super().__init__()
        self.setAutoFillBackground(True)
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        self.folder_scanner = FolderScanner(self.game_manager)
        self.settings_manager = SettingsManager()
        self.found_games_list = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        steam_tools_label = QLabel("Ferramentas da Steam")
        main_layout.addWidget(steam_tools_label)
        
        update_app_list_btn = QPushButton("Baixar/Atualizar Lista de Apps da Steam")
        update_app_list_btn.clicked.connect(self.update_steam_list)
        main_layout.addWidget(update_app_list_btn)

        auto_scan_label = QLabel("Buscas por Launcher")
        main_layout.addWidget(auto_scan_label)
        
        auto_scan_layout = QHBoxLayout()
        steam_btn = QPushButton("Varrer Biblioteca Steam")
        steam_btn.clicked.connect(self.scan_steam)
        auto_scan_layout.addWidget(steam_btn)
        epic_btn = QPushButton("Varrer Biblioteca Epic")
        epic_btn.clicked.connect(self.scan_epic)
        auto_scan_layout.addWidget(epic_btn)
        main_layout.addLayout(auto_scan_layout)

        manual_scan_label = QLabel("Busca Manual")
        main_layout.addWidget(manual_scan_label)
        
        manual_buttons_layout = QHBoxLayout()
        simple_scan_btn = QPushButton("📂 Selecionar Pasta (Rápido)")
        simple_scan_btn.clicked.connect(self.run_simple_scan_manual)
        manual_buttons_layout.addWidget(simple_scan_btn)
        deep_scan_btn = QPushButton("🔎 Selecionar Pasta (Completo)")
        deep_scan_btn.clicked.connect(self.run_deep_scan_manual)
        manual_buttons_layout.addWidget(deep_scan_btn)
        main_layout.addLayout(manual_buttons_layout)
        
        # --- SEÇÃO CORRIGIDA ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        results_label = QLabel("Resultados da Varredura:")
        main_layout.addWidget(results_label)

        self.results_list = QListWidget()
        main_layout.addWidget(self.results_list)

        action_layout = QHBoxLayout()
        select_all_btn = QPushButton("Marcar Todos")
        select_all_btn.clicked.connect(self.select_all)
        action_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Desmarcar Todos")
        deselect_all_btn.clicked.connect(self.deselect_all)
        action_layout.addWidget(deselect_all_btn)
        action_layout.addStretch()

        import_btn = QPushButton("✅ Adicionar Selecionados")
        import_btn.clicked.connect(self.import_selected_games)
        action_layout.addWidget(import_btn)
        
        main_layout.addLayout(action_layout)

    def update_steam_list(self):
        reply = self.main_window_ref.show_message_box(
            "Atualizar Lista de Apps",
            "Isso fará o download de um arquivo grande (~25MB) da Steam com todos os jogos disponíveis. Esta operação só precisa ser feita uma vez a cada vários meses.\n\nDeseja continuar?",
            "question",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success = steam_api.update_steam_app_list()
            if success:
                self.main_window_ref.show_message_box("Sucesso", "A lista de aplicativos da Steam foi atualizada com sucesso.", "info")
            else:
                self.main_window_ref.show_message_box("Erro", "Não foi possível baixar a lista de aplicativos. Verifique sua conexão com a internet ou tente mais tarde.", "warning")

    def _find_library_path(self, launcher_key, default_paths, dialog_title):
        saved_path = self.settings_manager.get_setting(launcher_key)
        if saved_path and os.path.isdir(saved_path):
            print(f"Usando caminho salvo para {launcher_key}: {saved_path}")
            return saved_path
        for path in default_paths:
            if os.path.isdir(path):
                print(f"Caminho padrão encontrado para {launcher_key}: {path}")
                self.settings_manager.save_setting(launcher_key, path)
                return path
        msg = f"Não foi possível encontrar a pasta de jogos da {dialog_title}. Por favor, aponte para a pasta correta."; self.main_window_ref.show_message_box("Pasta não encontrada", msg, "info")
        user_path = QFileDialog.getExistingDirectory(self, f"Localizar pasta de jogos da {dialog_title}")
        if user_path:
            self.settings_manager.save_setting(launcher_key, user_path)
            return user_path
        return None

    def scan_steam(self):
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        default_paths = [os.path.join(program_files_x86, "Steam", "steamapps", "common"), os.path.join(program_files, "Steam", "steamapps", "common")]
        steam_path = self._find_library_path("steam_common_path", default_paths, "Steam")
        if steam_path:
            self._execute_scan(self.folder_scanner.scan_folder_simple, steam_path)

    def scan_epic(self):
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        default_paths = [
            os.path.join(program_files, "Epic Games")
            # Adicione outros locais comuns se necessário, ex: "D:\\Epic Games"
        ]
        epic_path = self._find_library_path("epic_games_path", default_paths, "Epic Games")
        if epic_path:
            # Para a Epic, a busca completa costuma ser melhor.
            self._execute_scan(self.folder_scanner.scan_folder_deep, epic_path)

    def run_simple_scan_manual(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta (Busca Rápida)")
        if folder_path:
            self._execute_scan(self.folder_scanner.scan_folder_simple, folder_path)

    def run_deep_scan_manual(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta (Completa)")
        if folder_path:
            self._execute_scan(self.folder_scanner.scan_folder_deep, folder_path)

    def _execute_scan(self, scan_method, path):
        self.results_list.clear()
        loading_label = QLabel("Varrendo... Por favor, aguarde.", self)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setGeometry(self.rect()) # Cobre a aba inteira
        loading_label.show()
        QApplication.processEvents()

        self.found_games_list = scan_method(path)

        loading_label.hide()
        self.populate_results()
        
    def populate_results(self):
        self.results_list.clear()
        if not self.found_games_list:
            self.results_list.addItem("Nenhum novo jogo encontrado nesta pasta.")
            return
        for game in self.found_games_list:
            item = QListWidgetItem(self.results_list)
            checkbox = QCheckBox(f"{game['name']}  ({game['path']})")
            checkbox.setChecked(True)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, checkbox)

    def select_all(self):
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            widget = self.results_list.itemWidget(item)
            if isinstance(widget, QCheckBox): widget.setChecked(True)

    def deselect_all(self):
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            widget = self.results_list.itemWidget(item)
            if isinstance(widget, QCheckBox): widget.setChecked(False)
            
    def import_selected_games(self):
        selected_games = []
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            widget = self.results_list.itemWidget(item)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                # Corrigido para pegar o índice correto da lista de jogos encontrados
                selected_games.append(self.found_games_list[i])
        
        if not selected_games:
            self.main_window_ref.show_message_box("Aviso", "Nenhum jogo selecionado.", "warning")
            return

        added_count = 0
        self.results_list.clear()
        self.results_list.addItem("Importando... Isso pode levar alguns segundos.")
        self.main_window_ref.app.processEvents()

        for game in selected_games:
            artwork = None
            app_id = game.get("app_id") # Pega o app_id do jogo escaneado
            if app_id:
                artwork = steam_api.download_steam_artwork(app_id)
            
            image_path = artwork.get("image") if artwork else None
            background_path = artwork.get("background") if artwork else None
            header_path = artwork.get("header") if artwork else None

            paths_list = [{"path": game['path'], "display_name": os.path.basename(game['path'])}]
            
            # --- CHAMADA CORRIGIDA E COMPLETA ---
            self.game_manager.add_game(
                name=game['name'], 
                paths=paths_list, 
                image_path=image_path, 
                background_path=background_path, 
                header_path=header_path,
                source='steam', # Informa que a fonte é a Steam
                app_id=app_id    # Passa o AppID do jogo
            )
            added_count += 1
        
        self.main_window_ref.show_message_box("Sucesso", f"{added_count} jogo(s) adicionado(s) com sucesso!")
        self.main_window_ref.refresh_views()
        self.results_list.clear()