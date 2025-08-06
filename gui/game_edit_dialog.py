# gui/game_edit_dialog.py

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFormLayout, QGroupBox,
    QInputDialog, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from core.igdb_api import IGDB_API, download_and_save_images
from gui.igdb_search_dialog import IGDBSearchDialog

class GameEditDialog(QDialog):
    def __init__(self, game_id, game_manager, main_window_ref, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        self.game_id = game_id
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        self.igdb_api = IGDB_API()
        
        # --- INÍCIO DA CORREÇÃO ---
        # 1. Busca os dados completos do jogo usando o ID recebido.
        self.original_game_data = self.game_manager.get_game_by_id(self.game_id)
        if not self.original_game_data:
            # Medida de segurança caso o jogo não seja encontrado
            raise ValueError(f"Jogo com ID {self.game_id} não encontrado no banco de dados.")

        # 2. Cria uma cópia profunda dos dados para edição, evitando modificar o original.
        self.current_edited_game = self.original_game_data.copy()
        self.current_edited_game['paths'] = [p.copy() for p in self.original_game_data.get('paths', [])]
        # --- FIM DA CORREÇÃO ---

        self.setWindowTitle(f"Editando: {self.current_edited_game['name']}")
        self.setMinimumWidth(500)
        
        self._setup_edit_form_ui()

    def _setup_edit_form_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(self.current_edited_game.get("name", ""))
        form_layout.addRow("Nome:", self.name_input)

        tags_text = ", ".join(self.current_edited_game.get("tags", []))
        self.tags_input = QLineEdit(tags_text)
        form_layout.addRow("Tags:", self.tags_input)

        self.source_combo = QComboBox()
        current_source = self.current_edited_game.get("source", "local")
        try:
            icon_dir = "assets/icons/platform"
            available_sources = [os.path.splitext(f)[0] for f in os.listdir(icon_dir) if f.endswith(".svg")]
            for source_name in sorted(available_sources):
                self.source_combo.addItem(source_name.capitalize(), source_name)
                if source_name == current_source:
                    self.source_combo.setCurrentText(source_name.capitalize())
        except FileNotFoundError:
            self.source_combo.addItem(current_source.capitalize(), current_source)
        form_layout.addRow("Plataforma:", self.source_combo)

        paths_group_box = QGroupBox("Executáveis")
        self.paths_edit_layout = QVBoxLayout(paths_group_box)
        self._refresh_edit_paths_labels()
        form_layout.addRow(paths_group_box)

        btn_add_path = QPushButton("Adicionar Executável")
        btn_add_path.clicked.connect(self._edit_add_path)
        btn_remove_path = QPushButton("Remover Executável")
        btn_remove_path.clicked.connect(self._edit_remove_path)
        
        paths_button_layout = QHBoxLayout()
        paths_button_layout.addWidget(btn_add_path)
        paths_button_layout.addWidget(btn_remove_path)
        form_layout.addRow(paths_button_layout)

        self.img_btn = QPushButton("Alterar Pôster (Vertical)")
        self.img_btn.clicked.connect(self._edit_change_image)
        self.bg_btn = QPushButton("Alterar Fundo/Header (Horizontal)")
        self.bg_btn.clicked.connect(self._edit_change_background)
        
        images_button_layout = QHBoxLayout()
        images_button_layout.addWidget(self.img_btn)
        images_button_layout.addWidget(self.bg_btn)
        form_layout.addRow(images_button_layout)

        btn_search_online = QPushButton("🔎 Buscar e Preencher com IGDB")
        btn_search_online.clicked.connect(lambda: self._search_online_data(self.name_input))
        
        save_button = QPushButton("Salvar Alterações")
        save_button.clicked.connect(self._save_changes)
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        
        final_buttons_layout = QHBoxLayout()
        final_buttons_layout.addWidget(btn_search_online)
        final_buttons_layout.addStretch()
        final_buttons_layout.addWidget(cancel_button)
        final_buttons_layout.addWidget(save_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(final_buttons_layout)

    def _save_changes(self):
        new_name = self.name_input.text().strip()
        if not new_name or not self.current_edited_game.get("paths"):
            self.main_window_ref.show_message_box("Erro", "Nome e ao menos um executável são obrigatórios.", "warning")
            return

        self.current_edited_game["name"] = new_name
        self.current_edited_game["source"] = self.source_combo.currentData()
        tags_text = self.tags_input.text().strip()
        self.current_edited_game["tags"] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Passa os dados originais e os novos para a função de atualização
        self.game_manager.update_game(self.original_game_data, self.current_edited_game)
        self.accept()

    def _search_online_data(self, name_input_widget):
        game_name_to_search = name_input_widget.text()
        if not game_name_to_search:
            self.main_window_ref.show_message_box("Aviso", "Digite um nome de jogo para buscar.", "warning")
            return
        
        results = self.igdb_api.search_games(game_name_to_search)
        if not results:
            self.main_window_ref.show_message_box("Busca Online", f"Nenhum resultado encontrado para '{game_name_to_search}'.", "info")
            return
            
        results_dialog = IGDBSearchDialog(results, self)
        
        if results_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_game = results_dialog.get_selected_game()
            
            if selected_game:
                data_was_changed = False
                should_download_art = True
                if self.current_edited_game.get("image_path") or self.current_edited_game.get("background_path"):
                    reply = self.main_window_ref.show_message_box(
                        "Confirmar Substituição",
                        "Este jogo já possui artes locais. Deseja substituí-las com as artes do IGDB?",
                        "question",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.No:
                        should_download_art = False

                if should_download_art:
                    local_paths = download_and_save_images(selected_game)
                    if local_paths:
                        data_was_changed = True
                        self.current_edited_game.update(local_paths)

                self.name_input.setText(selected_game.get("name", self.current_edited_game.get("name")))
                self.tags_input.setText(", ".join(selected_game.get("genres", [])))
                self.current_edited_game.update(selected_game)
                data_was_changed = True

                if data_was_changed:
                    self.main_window_ref.show_message_box("Sucesso", "Dados preenchidos! Clique em 'Salvar Alterações' para confirmar.", "info")

    def _refresh_edit_paths_labels(self):
        for i in reversed(range(self.paths_edit_layout.count())):
            self.paths_edit_layout.itemAt(i).widget().deleteLater()
        
        paths = self.current_edited_game.get("paths", [])
        if paths:
            for d in paths:
                self.paths_edit_layout.addWidget(QLabel(f"• {d.get('display_name')}"))
        else:
            self.paths_edit_layout.addWidget(QLabel("(Nenhum executável)"))

    def _edit_add_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Executável")
        if not file_path: return
        
        display_name, ok = QInputDialog.getText(self, "Nome de Exibição", "Nome para este executável:", QLineEdit.EchoMode.Normal, os.path.basename(file_path))
        if ok and display_name.strip():
            self.current_edited_game["paths"].append({"path": file_path, "display_name": display_name.strip()})
            self._refresh_edit_paths_labels()

    def _edit_remove_path(self):
        paths = self.current_edited_game.get("paths", [])
        if not paths: return
        
        items = [d.get('display_name') for d in paths]
        item, ok = QInputDialog.getItem(self, "Remover Executável", "Selecione:", items, 0, False)
        if ok and item:
            self.current_edited_game["paths"] = [d for d in paths if d.get('display_name') != item]
            self._refresh_edit_paths_labels()

    def _edit_change_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Pôster", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.current_edited_game["image_path"] = file_path
            self.img_btn.setText(f"Pôster: {os.path.basename(file_path)}")

    def _edit_change_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Fundo", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.current_edited_game["background_path"] = file_path
            self.current_edited_game["header_path"] = file_path
            self.bg_btn.setText(f"Fundo: {os.path.basename(file_path)}")
