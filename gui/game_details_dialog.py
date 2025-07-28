# gui/game_details_dialog.py

import os
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QComboBox, QLineEdit, QFormLayout, QGroupBox,
    QInputDialog, QFileDialog, QWidget, QSpacerItem, QSizePolicy,
    QComboBox
)
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt6.QtCore import Qt, QPoint
from core import steam_api
from core.igdb_api import IGDB_API, download_and_save_images
from gui.igdb_search_dialog import IGDBSearchDialog

class GameDetailsDialog(QDialog):
    def __init__(self, game, game_manager, game_launcher, main_window_ref, parent=None):
        super().__init__(parent)
        # Pega as "flags" (configurações) atuais da janela
        flags = self.windowFlags()
        # Remove APENAS a flag do botão de ajuda, mantendo todas as outras
        self.setWindowFlags(flags & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.game = game
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref
        self.igdb_api = IGDB_API()
        
        self.setWindowTitle(self.game["name"])
        self.setFixedSize(800, 500)
        
        self.background_pixmap = None
        
        self.original_game_state = self.game.copy()
        self.original_game_state['paths'] = [p.copy() for p in self.game.get('paths', [])]
        
        self.current_edited_game = self.game.copy()
        self.current_edited_game['paths'] = [p.copy() for p in self.game.get('paths', [])]

        self._setup_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Checa se o pixmap existe E não é nulo/vazio (mais seguro)
        if self.background_pixmap and not self.background_pixmap.isNull():
            target_rect = self.rect()
            scaled_pixmap = self.background_pixmap.scaled(
                target_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
            )
            point = QPoint(
                (target_rect.width() - scaled_pixmap.width()) // 2,
                (target_rect.height() - scaled_pixmap.height()) // 2
            )
            painter.drawPixmap(point, scaled_pixmap)
        else:
            # Se não houver imagem, pinta um fundo sólido para garantir que não quebre.
            # Usamos uma cor fixa aqui, que corresponde ao nosso tema.
            painter.fillRect(self.rect(), QBrush(QColor("#1e1e1e")))

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30,20,30,20)
        
        overlay_panel = QWidget()
        self.main_layout.addWidget(overlay_panel)

        panel_layout = QHBoxLayout(overlay_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        panel_layout.setSpacing(30)

        cover_label = QLabel()
        cover_label.setFixedSize(250, 375)
        panel_layout.addWidget(cover_label)

        if self.game.get("image") and os.path.exists(self.game["image"]):
            pixmap = QPixmap(self.game["image"])
            cover_label.setPixmap(pixmap.scaled(cover_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            cover_label.setText("Sem Capa")
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        right_column_layout = QVBoxLayout()
        panel_layout.addLayout(right_column_layout, 1)

        right_column_layout.addStretch(1)

        name_label = QLabel(self.game["name"])
        name_label.setObjectName("DetailsGameTitle") # Nome para o QSS
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_column_layout.addWidget(name_label)
        
        total_seconds = self.game.get("total_playtime", 0)
        playtime_str = self._format_playtime(total_seconds)
        playtime_label = QLabel(f"🕒 {playtime_str}"); 
        right_column_layout.addWidget(playtime_label)

        tags_layout = QHBoxLayout(); tags_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tags = self.game.get("tags", [])
        if tags:
            for tag_text in tags:
                tag_label = QLabel(tag_text)
                tags_layout.addWidget(tag_label)
        right_column_layout.addLayout(tags_layout)

        right_column_layout.addStretch(1)

        paths = self.game.get("paths", [])
        if len(paths) > 1:
            self.execcombo = QComboBox()
            for d in paths:
                self.execcombo.addItem(d.get("display_name", os.path.basename(d["path"])), userData=d["path"])
            right_column_layout.addWidget(self.execcombo)

        btn_play = QPushButton("▶ Jogar")
        if len(paths) > 1:
            btn_play.clicked.connect(self._launch_selected_game)
        elif len(paths) == 1:
            btn_play.clicked.connect(lambda: self._launch_game(paths[0]["path"]))
        else:
            btn_play.setEnabled(False)
        right_column_layout.addWidget(btn_play)
        
        action_buttons_layout = QHBoxLayout()
        
        is_favorite = self.game.get("favorite", False)
        fav_text = "⭐ Favorito" if is_favorite else "⭐ Favoritar"
        btn_fav = QPushButton(fav_text); btn_fav.clicked.connect(self._toggle_favorite)
        
        btn_edit = QPushButton("✏️ Editar"); btn_edit.clicked.connect(self._edit_game_dialog)
        
        btn_delete = QPushButton("🗑️ Excluir"); btn_delete.clicked.connect(self._delete_game)

        action_buttons_layout.addWidget(btn_fav); action_buttons_layout.addWidget(btn_edit); action_buttons_layout.addWidget(btn_delete)
        right_column_layout.addLayout(action_buttons_layout)

        bg_path = self.game.get("background")
        if bg_path and os.path.exists(bg_path):
            self.background_pixmap = QPixmap(bg_path)

    def _edit_game_dialog(self):
        edit_dialog = QDialog(self)
        # Pega as flags atuais da janela de edição
        flags = edit_dialog.windowFlags()
        # Remove o botão de ajuda de contexto
        edit_dialog.setWindowFlags(flags & ~Qt.WindowType.WindowContextHelpButtonHint)
        edit_dialog.setWindowTitle(f"Editar {self.current_edited_game['name']}")
        edit_dialog.setMinimumWidth(400)
        
        edit_layout = QFormLayout()

        name_input = QLineEdit(self.current_edited_game["name"])
        edit_layout.addRow("Nome:", name_input)

        tags_text = ", ".join(self.current_edited_game.get("tags", []))
        self.tags_input = QLineEdit(tags_text)
        self.tags_input.setPlaceholderText("RPG, Indie, Ação... (separadas por vírgula)")
        edit_layout.addRow("Tags:", self.tags_input)

        self.source_combo = QComboBox()

        available_sources = []
        try:
            icon_dir = "assets/icons/platform"
            available_sources = [os.path.splitext(f)[0] for f in os.listdir(icon_dir) if f.endswith(".svg")]
        except FileNotFoundError:
            available_sources = ["local", "steam", "epic"] # Fallback

        current_source = self.current_edited_game.get("source", "local")

        for source_name in available_sources:
            self.source_combo.addItem(source_name.capitalize(), source_name)
            if source_name == current_source:
                self.source_combo.setCurrentText(source_name.capitalize())

        edit_layout.addRow("Plataforma:", self.source_combo)

        paths_group_box = QGroupBox("Executáveis"); 
        self.paths_edit_layout = QVBoxLayout(); paths_group_box.setLayout(self.paths_edit_layout)
        edit_layout.addRow(paths_group_box); self._refresh_edit_paths_labels()

        btn_add_path = QPushButton("Adicionar Executável"); btn_add_path.clicked.connect(self._edit_add_path)
        edit_layout.addRow(btn_add_path)

        btn_remove_path = QPushButton("Remover Selecionado"); btn_remove_path.clicked.connect(self._edit_remove_path)
        edit_layout.addRow(btn_remove_path)

        img_path = self.current_edited_game.get('image')
        img_text = os.path.basename(img_path) if img_path else 'Nenhuma selecionada'
        self.img_btn = QPushButton(f"Alterar Pôster (logo): {img_text}")
        self.img_btn.clicked.connect(self._edit_change_image)
        edit_layout.addRow(self.img_btn)

        bg_path = self.current_edited_game.get('background')
        bg_text = os.path.basename(bg_path) if bg_path else 'Nenhuma selecionada'
        self.bg_btn = QPushButton(f"Alterar Fundo (hero): {bg_text}")
        self.bg_btn.clicked.connect(self._edit_change_background)
        edit_layout.addRow(self.bg_btn)
        
        btn_search_online = QPushButton("🔎 Buscar Informações Online (IGDB)")
        btn_search_online.clicked.connect(lambda: self._search_online_data(name_input)) # Conecta ao novo método
        edit_layout.addRow(btn_search_online)

        btn_save = QPushButton("Salvar Alterações")
        btn_save.clicked.connect(lambda: self._save_edited_game(name_input.text(), edit_dialog))
        edit_layout.addRow(btn_save)

        edit_dialog.setLayout(edit_layout)
        if edit_dialog.exec():
            self.main_window_ref.refresh_views()
            self.accept()

    def _search_online_data(self, name_input_widget):
        """Busca o jogo no IGDB e preenche os campos."""
        game_name_to_search = name_input_widget.text()
        if not game_name_to_search:
            self.main_window_ref.show_message_box("Aviso", "Digite um nome de jogo para buscar.", "warning")
            return
        
        print(f"Buscando '{game_name_to_search}' no IGDB...")
        results = self.igdb_api.search_games(game_name_to_search)
        
        if not results:
            self.main_window_ref.show_message_box("Busca Online", f"Nenhum resultado encontrado para '{game_name_to_search}'.", "info")
            return
            
        # Mostra a janela de resultados
        results_dialog = IGDBSearchDialog(results, self)
        if results_dialog.exec():
            selected_game = results_dialog.get_selected_game()
            if selected_game:
                print("Jogo selecionado:", selected_game)

                # --- ATUALIZA A UI E OS DADOS ---
                name_input_widget.setText(selected_game["name"])

                # ... (atualiza o dicionário com nome, summary, etc.)
                self.tags_input.setText(", ".join(selected_game["genres"]))

                # --- BLOCO NOVO PARA DOWNLOAD ---
                print("Baixando artes do jogo...")
                local_paths = download_and_save_images(selected_game)

                # Atualiza o dicionário com os caminhos LOCAIS das imagens
                self.current_edited_game.update(local_paths)

                # Atualiza os botões na UI para mostrar que as imagens foram encontradas
                if "image_path" in local_paths:
                    self.img_btn.setText(f"Alterar Pôster: {os.path.basename(local_paths['image_path'])}")
                if "background_path" in local_paths:
                    self.bg_btn.setText(f"Alterar Fundo: {os.path.basename(local_paths['background_path'])}")

                print("Download de artes concluído.")

                
                # --- ATUALIZA A UI E OS DADOS ---
                # Atualiza o nome na caixa de texto
                name_input_widget.setText(selected_game["name"])
                
                # Atualiza o dicionário interno com os novos dados
                self.current_edited_game["name"] = selected_game["name"]
                self.current_edited_game["summary"] = selected_game["summary"]
                self.current_edited_game["igdb_id"] = str(selected_game["igdb_id"])
                
                # Converte a lista de gêneros para uma string separada por vírgula
                self.tags_input.setText(", ".join(selected_game["genres"]))
                
                # Guarda as URLs para download (faremos o download no próximo passo)
                self.current_edited_game["cover_url"] = selected_game["cover_url"]
                self.current_edited_game["screenshot_urls"] = selected_game["screenshot_urls"]
                
                self.main_window_ref.show_message_box("Sucesso", "Dados do jogo preenchidos! Clique em 'Salvar Alterações' para confirmar.", "info")

    # O resto dos métodos (helpers) da classe continuam aqui, devidamente indentados
    def _format_playtime(self, total_seconds):
        if total_seconds <= 0: return "Nenhum tempo registrado"
        hours, rem = divmod(total_seconds, 3600); minutes, _ = divmod(rem, 60)
        if hours > 0: return f"~{int(hours)}h e {int(minutes)}min"
        return f"{int(minutes)}min"

    def _launch_selected_game(self):
        self._launch_game(self.execcombo.currentData())

    def _launch_game(self, path):
        result, data = self.game_launcher.launch_game(self.game, path)
        if result == "running": self.main_window_ref.show_message_box("Jogo em execução", f"O jogo '{os.path.basename(path)}' já está em execução.", "info")
        elif result == "error": self.main_window_ref.show_message_box("Erro ao abrir", f"Não foi possível abrir o jogo:\n{data}", "warning")
        else:
            self.main_window_ref.start_tracking_game(result, data); self.main_window_ref.refresh_views(); self.accept()

    def _toggle_favorite(self):
        self.game_manager.toggle_favorite(self.game); self.main_window_ref.refresh_views(); self.accept()

    def _refresh_edit_paths_labels(self):
        for i in reversed(range(self.paths_edit_layout.count())):
            widget = self.paths_edit_layout.itemAt(i).widget();
            if widget: widget.setParent(None)
        if self.current_edited_game.get("paths"):
            for d in self.current_edited_game["paths"]:
                lbl = QLabel(f"• {d.get('display_name', '')} — {os.path.basename(d['path'])}"); lbl.setWordWrap(True); self.paths_edit_layout.addWidget(lbl)
        else:
            lbl = QLabel("(Nenhum executável adicionado)"); self.paths_edit_layout.addWidget(lbl)

    def _edit_add_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar executável")
        if file_path:
            name, ok = QInputDialog.getText(self, "Nome de Exibição", "Digite um nome para este executável:", QLineEdit.Normal, os.path.basename(file_path))
            if ok and name.strip():
                if not any(d['path'] == file_path for d in self.current_edited_game["paths"]):
                    self.current_edited_game["paths"].append({"path": file_path, "display_name": name.strip()}); self._refresh_edit_paths_labels()

    def _edit_remove_path(self):
        if not self.current_edited_game.get("paths"): self.main_window_ref.show_message_box("Erro", "Não há executáveis para remover.", "warning"); return
        items = [f"{d.get('display_name', '')} - {os.path.basename(d['path'])}" for d in self.current_edited_game["paths"]]
        item, ok = QInputDialog.getItem(self, "Remover Executável", "Selecione o executável para remover:", items, 0, False)
        if ok and item:
            for idx, d in enumerate(self.current_edited_game["paths"]):
                if f"{d.get('display_name', '')} - {os.path.basename(d['path'])}" == item:
                    del self.current_edited_game["paths"][idx]; break
            self._refresh_edit_paths_labels()

    def _edit_change_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar imagem", filter="Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:
            self.current_edited_game["image"] = file_path; sender = self.sender()
            if sender: sender.setText(f"Alterar Pôster (logo): {os.path.basename(file_path)}")

    def _edit_change_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar imagem de fundo", filter="Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:
            self.current_edited_game["background"] = file_path; sender = self.sender()
            if sender: sender.setText(f"Alterar Fundo (hero): {os.path.basename(file_path)}")

    def _save_edited_game(self, new_name, dialog):
        new_name = new_name.strip()
        if not new_name or not self.current_edited_game["paths"]: self.main_window_ref.show_message_box("Erro", "Nome e ao menos um executável são obrigatórios.", "warning"); return
        self.current_edited_game["name"] = new_name
        tags_text = self.tags_input.text().strip()
        self.current_edited_game["tags"] = [tag.strip() for tag in tags_text.split(',')] if tags_text else []
        self.current_edited_game["source"] = self.source_combo.currentData()
        
        self.game_manager.update_game(self.original_game_state, self.current_edited_game)
        dialog.accept()

    def _delete_game(self):
        reply = self.main_window_ref.show_message_box("Confirmar exclusão", f"Tem certeza que deseja excluir '{self.game['name']}'?", "question", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: # <--- CORREÇÃO APLICADA AQUI
            self.game_manager.delete_game(self.game)
            self.main_window_ref.refresh_views()
            self.accept()
