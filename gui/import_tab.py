# gui/import_tab.py

import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QCheckBox, QLabel, QMessageBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt

from core.folder_scanner import SteamScanner, LocalGameScanner
from core.settings_manager import SettingsManager
from core.steam_app_list import find_appid_by_name, update_steam_app_list
from core.artwork_manager import download_steam_artwork
from gui.metadata_review_dialog import MetadataReviewDialog
from core.igdb_api import IGDB_API, download_and_save_images
from gui.igdb_search_dialog import IGDBSearchDialog
from core.steam_web_api import get_owned_games

class ImportTab(QWidget):
    def __init__(self, game_manager, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        
        self.steam_scanner = SteamScanner(self.game_manager)
        self.local_scanner = LocalGameScanner(self.game_manager)
        self.igdb_api = IGDB_API()
        
        self.settings_manager = SettingsManager()
        self.found_games_list = []
        
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        sync_label = QLabel("Sincronização de Jogos")
        main_layout.addWidget(sync_label)
        
        sync_layout = QHBoxLayout()
        # --- INÍCIO DA ALTERAÇÃO ---
        # Botão único para toda a sincronização da Steam
        self.sync_steam_library_btn = QPushButton("Sincronizar Biblioteca Steam")
        self.sync_steam_library_btn.setToolTip("Busca todos os seus jogos, baixa artes e verifica quais estão instalados.")
        self.sync_steam_library_btn.clicked.connect(self.run_full_steam_sync)
        sync_layout.addWidget(self.sync_steam_library_btn)
        # --- FIM DA ALTERAÇÃO ---

        main_layout.addLayout(sync_layout)

        metadata_label = QLabel("Ferramentas de Metadados")
        main_layout.addWidget(metadata_label)
        metadata_layout = QHBoxLayout()
        self.metadata_btn = QPushButton("Buscar Metadados Faltantes (Steam/IGDB)")
        self.metadata_btn.setToolTip("Busca artes e informações para jogos que não as possuem.")
        self.metadata_btn.clicked.connect(self.run_metadata_search)
        metadata_layout.addWidget(self.metadata_btn)
        main_layout.addLayout(metadata_layout)

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

    # --- FUNÇÃO ATUALIZADA ---
    def run_full_steam_sync(self):
        """Orquestra a sincronização completa da biblioteca Steam em um único passo."""
        profile_data = self.main_window_ref.profile_manager.get_data()
        api_key = profile_data.get('steam_api_key')
        steam_id = profile_data.get('steam_id_64')

        if not api_key or not steam_id:
            self.main_window_ref.show_message_box("Conta não Vinculada", 
                                                 "Por favor, vincule sua conta Steam na aba de Configurações para usar esta funcionalidade.", 
                                                 "warning")
            return

        self.main_window_ref.show_loading_overlay("Buscando sua biblioteca na Steam...")
        QApplication.processEvents()

        owned_games = get_owned_games(api_key, steam_id)

        if owned_games is None:
            self.main_window_ref.hide_loading_overlay()
            self.main_window_ref.show_message_box("Erro de API", "Não foi possível buscar a lista de jogos. Verifique sua Chave de API, SteamID64 e conexão.", "critical")
            return
        
        self.main_window_ref.show_loading_overlay("Sincronizando jogos e artes...")
        QApplication.processEvents()
        self.game_manager.sync_full_steam_library(owned_games)

        self.main_window_ref.show_loading_overlay("Verificando jogos instalados...")
        QApplication.processEvents()
        self.steam_scanner.sync_steam_games()

        self.main_window_ref.hide_loading_overlay()
        self.main_window_ref.show_message_box("Sucesso", "Sua biblioteca Steam foi completamente sincronizada!", "info")
        self.main_window_ref.refresh_views()
    
    # ... (O resto do seu código pode permanecer o mesmo) ...
    def run_metadata_search(self):
        self.main_window_ref.show_loading_overlay("Buscando jogos sem arte...")
        QApplication.processEvents()
        update_steam_app_list()
        all_games = self.game_manager.get_all_games()
        games_to_search = [g for g in all_games if not g.get('image_path')]
        if not games_to_search:
            self.main_window_ref.hide_loading_overlay()
            self.main_window_ref.show_message_box("Tudo Certo", "Todos os jogos na sua biblioteca já possuem uma imagem de capa.", "info")
            return
        suggestions = []
        self.main_window_ref.show_loading_overlay("Procurando correspondências...")
        for game in games_to_search:
            appid = find_appid_by_name(game['name'])
            if appid:
                suggestion = {
                    'game_id': game['id'], 'original_name': game['name'], 'suggestion_name': game['name'], 
                    'source': 'steam', 'appid': appid,
                    'preview_url': f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
                }
                suggestions.append(suggestion)
                continue
            igdb_results = self.igdb_api.search_games(game['name'])
            if igdb_results:
                best_match = igdb_results[0]
                preview_url = best_match.get('cover_url', '')
                if preview_url:
                    preview_url = preview_url.replace('t_thumb', 't_cover_big')
                suggestion = {
                    'game_id': game['id'], 'original_name': game['name'], 'suggestion_name': best_match.get('name', 'N/A'),
                    'source': 'igdb', 'igdb_data': best_match, 'preview_url': preview_url
                }
                suggestions.append(suggestion)
        self.main_window_ref.hide_loading_overlay()
        if not suggestions:
            self.main_window_ref.show_message_box("Nenhum Resultado", "Não foi possível encontrar correspondências para os jogos sem arte.", "info")
            return
        dialog = MetadataReviewDialog(suggestions, self.igdb_api, self)
        if dialog.exec():
            approved_suggestions = dialog.get_approved_suggestions()
            if approved_suggestions:
                self.apply_metadata(approved_suggestions)

    def apply_metadata(self, suggestions):
        self.main_window_ref.show_loading_overlay("Aplicando metadados...")
        QApplication.processEvents()
        applied_count = 0
        for s in suggestions:
            if s['source'] == 'steam':
                artwork_paths = download_steam_artwork(s['appid'])
                if artwork_paths:
                    self.game_manager.update_game_artwork(
                        game_id=s['game_id'], app_id=s['appid'],
                        image_path=artwork_paths.get('image_path'),
                        background_path=artwork_paths.get('background_path'),
                        header_path=artwork_paths.get('header_path')
                    )
                    applied_count += 1
            elif s['source'] == 'igdb':
                original_game_data = self.game_manager.get_game_by_id(s['game_id'])
                if not original_game_data: continue
                artwork_paths = download_and_save_images(s['igdb_data'])
                new_game_data = s['igdb_data'].copy()
                new_game_data.update(artwork_paths)
                self.game_manager.update_game(original_game_data, new_game_data)
                applied_count += 1
        self.main_window_ref.hide_loading_overlay()
        self.main_window_ref.show_message_box("Sucesso", f"Metadados aplicados a {applied_count} jogo(s).", "info")
        self.main_window_ref.refresh_views()

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
        if not self.found_games_list: self.results_list.addItem("Nenhum novo jogo encontrado nesta pasta."); return
        for game in self.found_games_list:
            item = QListWidgetItem(self.results_list)
            checkbox = QCheckBox(f"{game['name']}  ({game['path']})"); checkbox.setChecked(True)
            self.results_list.addItem(item); self.results_list.setItemWidget(item, checkbox)

    def select_all(self):
        for i in range(self.results_list.count()):
            item = self.results_list.item(i); widget = self.results_list.itemWidget(item)
            if isinstance(widget, QCheckBox): widget.setChecked(True)

    def deselect_all(self):
        for i in range(self.results_list.count()):
            item = self.results_list.item(i); widget = self.results_list.itemWidget(item)
            if isinstance(widget, QCheckBox): widget.setChecked(False)
            
    def import_selected_games(self):
        selected_games = [self.found_games_list[i] for i in range(self.results_list.count()) if isinstance(widget := self.results_list.itemWidget(self.results_list.item(i)), QCheckBox) and widget.isChecked()]
        if not selected_games: self.main_window_ref.show_message_box("Aviso", "Nenhum jogo selecionado.", "warning"); return
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
