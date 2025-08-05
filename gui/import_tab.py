# gui/import_tab.py

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QCheckBox, QLabel, QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt

# Removido QThread e workers
from core.folder_scanner import SteamScanner, LocalGameScanner
from core.settings_manager import SettingsManager

class ImportTab(QWidget):
    def __init__(self, game_manager, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        
        self.steam_scanner = SteamScanner(self.game_manager)
        self.local_scanner = LocalGameScanner(self.game_manager)
        
        self.settings_manager = SettingsManager()
        self.found_games_list = []
        
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        sync_label = QLabel("Sincronização Automática")
        main_layout.addWidget(sync_label)
        
        sync_layout = QHBoxLayout()
        self.steam_sync_btn = QPushButton("Sincronizar com a Steam")
        self.steam_sync_btn.setToolTip("Verifica jogos da Steam instalados, baixa artes e atualiza status.")
        self.steam_sync_btn.clicked.connect(self.run_steam_sync)
        sync_layout.addWidget(self.steam_sync_btn)
        
        main_layout.addLayout(sync_layout)

        # O resto da UI continua igual...
        manual_scan_label = QLabel("Adicionar Jogos Locais (Busca Manual)")
        main_layout.addWidget(manual_scan_label)
        manual_buttons_layout = QHBoxLayout()
        simple_scan_btn = QPushButton("📂 Selecionar Pasta (Busca Rápida)")
        simple_scan_btn.clicked.connect(self.run_simple_scan_manual)
        manual_buttons_layout.addWidget(simple_scan_btn)
        deep_scan_btn = QPushButton("🔎 Selecionar Pasta (Busca Completa)")
        deep_scan_btn.clicked.connect(self.run_deep_scan_manual)
        manual_buttons_layout.addWidget(deep_scan_btn)
        main_layout.addLayout(manual_buttons_layout)
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)
        results_label = QLabel("Resultados da Busca Manual:")
        main_layout.addWidget(results_label)
        self.results_list = QListWidget()
        main_layout.addWidget(self.results_list)
        action_layout = QHBoxLayout()
        select_all_btn = QPushButton("Marcar Todos"); select_all_btn.clicked.connect(self.select_all)
        action_layout.addWidget(select_all_btn)
        deselect_all_btn = QPushButton("Desmarcar Todos"); deselect_all_btn.clicked.connect(self.deselect_all)
        action_layout.addWidget(deselect_all_btn)
        action_layout.addStretch()
        import_btn = QPushButton("✅ Adicionar Selecionados"); import_btn.clicked.connect(self.import_selected_games)
        action_layout.addWidget(import_btn)
        main_layout.addLayout(action_layout)
        main_layout.addStretch()

    def run_steam_sync(self):
        """Executa a sincronização da Steam diretamente na thread principal."""
        self.main_window_ref.show_loading_overlay("Sincronizando com a Steam...")
        # Força a UI a processar eventos e mostrar a tela de carregamento
        QApplication.processEvents()

        try:
            # Chama o método de sincronização diretamente
            self.steam_scanner.sync_steam_games()
            
            # Mensagem de sucesso
            self.main_window_ref.show_message_box(
                "Sucesso", 
                "Sincronização com a Steam concluída! Sua biblioteca foi atualizada.", 
                "info"
            )
        except Exception as e:
            # Mostra um erro caso algo dê errado durante a sincronização
            self.main_window_ref.show_message_box("Erro na Sincronização", str(e), "critical")
        finally:
            # Garante que a tela de carregamento seja sempre escondida
            self.main_window_ref.hide_loading_overlay()
            # Atualiza as visualizações da biblioteca
            self.main_window_ref.refresh_views()
    
    # O resto das funções (busca manual, etc.) continua igual...
    def run_simple_scan_manual(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta (Busca Rápida)")
        if folder_path: self._execute_local_scan(self.local_scanner.scan_folder, folder_path, is_deep=False)

    def run_deep_scan_manual(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta (Completa)")
        if folder_path: self._execute_local_scan(self.local_scanner.scan_folder, folder_path, is_deep=True)

    def _execute_local_scan(self, scan_method, path, is_deep):
        self.results_list.clear()
        self.main_window_ref.show_loading_overlay("Buscando jogos locais...")
        QApplication.processEvents()
        self.found_games_list = scan_method(path, is_deep_scan=is_deep)
        self.main_window_ref.hide_loading_overlay()
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
                selected_games.append(self.found_games_list[i])
        if not selected_games:
            self.main_window_ref.show_message_box("Aviso", "Nenhum jogo selecionado.", "warning")
            return
        self.main_window_ref.show_loading_overlay("Importando jogos...")
        QApplication.processEvents()
        added_count = 0
        for game in selected_games:
            paths_list = [{"path": game['path'], "display_name": os.path.basename(game['path'])}]
            self.game_manager.add_game(name=game['name'], paths=paths_list, source='local')
            added_count += 1
        self.main_window_ref.hide_loading_overlay()
        self.main_window_ref.show_message_box("Sucesso", f"{added_count} jogo(s) local(is) adicionado(s) com sucesso!")
        self.main_window_ref.refresh_views()
        self.results_list.clear()
