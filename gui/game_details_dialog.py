# gui/game_details_dialog.py

import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QComboBox, QLineEdit, QFormLayout, QGroupBox,
    QInputDialog, QFileDialog, QWidget,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint

# Suas importações personalizadas
from core.theme import current_theme
from core import steam_api


class GameDetailsDialog(QDialog):
    def __init__(self, game, game_manager, game_launcher, main_window_ref, parent=None):
        super().__init__(parent)
        # Pega as "flags" (configurações) atuais da janela
        flags = self.windowFlags()
        # Remove APENAS a flag do botão de ajuda, mantendo todas as outras
        self.setWindowFlags(flags & ~Qt.WindowContextHelpButtonHint)
        self.game = game
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref
        
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
        if self.background_pixmap:
            target_rect = self.rect()
            scaled_pixmap = self.background_pixmap.scaled(
                target_rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            point = QPoint(
                (target_rect.width() - scaled_pixmap.width()) // 2,
                (target_rect.height() - scaled_pixmap.height()) // 2
            )
            painter.drawPixmap(point, scaled_pixmap)
        else:
            painter.fillRect(self.rect(), QBrush(QColor(current_theme['background'])))

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        overlay_panel = QWidget()
        overlay_color = current_theme['overlay_background']
        r, g, b, a = overlay_color.getRgb()
        overlay_panel.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {a});")
        self.main_layout.addWidget(overlay_panel)

        panel_layout = QHBoxLayout(overlay_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        panel_layout.setSpacing(30)

        cover_label = QLabel()
        cover_label.setFixedSize(250, 375)
        cover_label.setStyleSheet("border-radius: 10px;")
        panel_layout.addWidget(cover_label)

        if self.game.get("image") and os.path.exists(self.game["image"]):
            pixmap = QPixmap(self.game["image"])
            cover_label.setPixmap(pixmap.scaled(cover_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            cover_label.setStyleSheet("background-color: #111; border-radius: 10px; color: #888; font-weight: bold;")
            cover_label.setText("Sem Capa")
            cover_label.setAlignment(Qt.AlignCenter)
        
        right_column_layout = QVBoxLayout()
        panel_layout.addLayout(right_column_layout, 1)

        right_column_layout.addStretch(1)
        name_label = QLabel(self.game["name"]); name_label.setStyleSheet("font-size: 34px; font-weight: bold; color: white;"); name_label.setWordWrap(True); name_label.setAlignment(Qt.AlignCenter)
        right_column_layout.addWidget(name_label)
        
        total_seconds = self.game.get("total_playtime", 0)
        playtime_str = self._format_playtime(total_seconds)
        playtime_label = QLabel(f"🕒 {playtime_str}"); playtime_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ccc; margin-top: 10px; margin-bottom: 10px;"); playtime_label.setAlignment(Qt.AlignCenter)
        right_column_layout.addWidget(playtime_label)

        tags_layout = QHBoxLayout(); tags_layout.setAlignment(Qt.AlignCenter)
        tags = self.game.get("tags", [])
        if tags:
            for tag_text in tags:
                tag_label = QLabel(tag_text)
                tag_label.setStyleSheet(f"QLabel {{ background-color: {current_theme['accent'].name()}; color: white; padding: 4px 8px; border-radius: 8px; font-size: 12px; font-weight: bold; }}")
                tags_layout.addWidget(tag_label)
        right_column_layout.addLayout(tags_layout)

        right_column_layout.addStretch(1)

        paths = self.game.get("paths", [])
        if len(paths) > 1:
            self.exec_combo = QComboBox()
            self.exec_combo.setStyleSheet("QComboBox { background-color: #333; color: white; padding: 8px; border-radius: 5px; }")
            for d in paths:
                self.exec_combo.addItem(d.get("display_name", os.path.basename(d["path"])), userData=d["path"])
            right_column_layout.addWidget(self.exec_combo)

        btn_play = QPushButton("▶ Jogar")
        btn_play.setStyleSheet(f"padding: 12px; font-size: 16px; font-weight: bold; background-color: {current_theme['accent_success'].name()}; color: white; border-radius: 5px;")
        if len(paths) > 1:
            btn_play.clicked.connect(self._launch_selected_game)
        elif len(paths) == 1:
            btn_play.clicked.connect(lambda: self._launch_game(paths[0]["path"]))
        else:
            btn_play.setEnabled(False)
        right_column_layout.addWidget(btn_play)
        
        action_buttons_layout = QHBoxLayout()
        button_style = "QPushButton { background-color: #444; color: white; border-radius: 5px; padding: 8px; } QPushButton:hover { background-color: #555; }"
        
        is_favorite = self.game.get("favorite", False)
        fav_text = "⭐ Favorito" if is_favorite else "⭐ Favoritar"
        btn_fav = QPushButton(fav_text); btn_fav.setStyleSheet(button_style); btn_fav.clicked.connect(self._toggle_favorite)
        
        btn_edit = QPushButton("✏️ Editar"); btn_edit.setStyleSheet(button_style); btn_edit.clicked.connect(self._edit_game_dialog)
        
        btn_delete = QPushButton("🗑️ Excluir"); btn_delete.setStyleSheet(button_style); btn_delete.clicked.connect(self._delete_game)

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
        edit_dialog.setWindowFlags(flags & ~Qt.WindowContextHelpButtonHint)
        edit_dialog.setWindowTitle(f"Editar {self.current_edited_game['name']}")
        edit_dialog.setStyleSheet(f"background-color: {current_theme['background'].name()}; color: white;")
        edit_dialog.setMinimumWidth(400)
        
        edit_layout = QFormLayout()

        name_input = QLineEdit(self.current_edited_game["name"])
        edit_layout.addRow("Nome:", name_input)

        tags_text = ", ".join(self.current_edited_game.get("tags", []))
        self.tags_input = QLineEdit(tags_text)
        self.tags_input.setPlaceholderText("RPG, Indie, Ação... (separadas por vírgula)")
        edit_layout.addRow("Tags:", self.tags_input)

        paths_group_box = QGroupBox("Executáveis"); paths_group_box.setStyleSheet("color: white;")
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
        
        btn_search_steam = QPushButton("🔎 Buscar Arte da Steam por Nome")
        btn_search_steam.setStyleSheet(f"background-color: {current_theme['accent'].name()}; color: white; padding: 8px;")
        btn_search_steam.clicked.connect(self._search_steam_artwork)
        edit_layout.addRow(btn_search_steam)

        btn_save = QPushButton("Salvar Alterações")
        btn_save.setStyleSheet(f"background-color: {current_theme['accent_success_bright'].name()}; color: {current_theme['text_inverted'].name()}; font-weight: bold; padding: 8px;")
        btn_save.clicked.connect(lambda: self._save_edited_game(name_input.text(), edit_dialog))
        edit_layout.addRow(btn_save)

        edit_dialog.setLayout(edit_layout)
        if edit_dialog.exec_():
            self.main_window_ref.refresh_views()
            self.accept()

    def _search_steam_artwork(self):
        app_list_path = os.path.join(steam_api.get_app_root_path(), "steam_app_list.json")
        if not os.path.exists(app_list_path):
            self.main_window_ref.show_message_box("Aviso", "A lista de aplicativos da Steam não foi baixada. Vá para a aba 'Importar Jogos' e clique em 'Baixar/Atualizar Lista de Apps da Steam' primeiro.", "warning")
            return

        current_name = self.current_edited_game.get("name", "")
        game_name, ok = QInputDialog.getText(self, "Buscar Arte", "Digite o nome exato do jogo para buscar na Steam:", text=current_name)

        if not ok or not game_name.strip(): return

        logging.info(f"Buscando AppID para '{game_name}'...")
        app_id = steam_api.find_appid_by_name(game_name)

        if not app_id:
            self.main_window_ref.show_message_box("Não Encontrado", f"Nenhum jogo correspondente a '{game_name}' foi encontrado na lista da Steam.", "info")
            return

        logging.info(f"AppID {app_id} encontrado. Baixando artes...")
        artwork = steam_api.download_steam_artwork(app_id)

        if not artwork:
            self.main_window_ref.show_message_box("Erro", "Não foi possível baixar as artes para este jogo, mesmo com o AppID encontrado.", "warning")
            return
            
        self.current_edited_game["image"] = artwork.get("image")
        self.current_edited_game["background"] = artwork.get("background")
        self.current_edited_game["header_path"] = artwork.get("header")
        
        img_text = os.path.basename(artwork.get("image", "")) or "Nenhuma"
        bg_text = os.path.basename(artwork.get("background", "")) or "Nenhuma"
        self.img_btn.setText(f"Alterar Pôster (logo): {img_text}")
        self.bg_btn.setText(f"Alterar Fundo (hero): {bg_text}")
        self.main_window_ref.show_message_box("Sucesso!", "Artes da Steam baixadas e aplicadas. Clique em 'Salvar Alterações' para confirmar.", "info")

    # O resto dos métodos (helpers) da classe continuam aqui, devidamente indentados
    def _format_playtime(self, total_seconds):
        if total_seconds <= 0: return "Nenhum tempo registrado"
        hours, rem = divmod(total_seconds, 3600); minutes, _ = divmod(rem, 60)
        if hours > 0: return f"~{int(hours)}h e {int(minutes)}min"
        return f"{int(minutes)}min"

    def _launch_selected_game(self):
        self._launch_game(self.exec_combo.currentData())

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
                lbl = QLabel(f"• {d.get('display_name', '')} — {os.path.basename(d['path'])}"); lbl.setStyleSheet("color: white;"); lbl.setWordWrap(True); self.paths_edit_layout.addWidget(lbl)
        else:
            lbl = QLabel("(Nenhum executável adicionado)"); lbl.setStyleSheet("color: #777; font-style: italic;"); self.paths_edit_layout.addWidget(lbl)

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
        self.game_manager.update_game(self.original_game_state, self.current_edited_game)
        dialog.accept()

    def _delete_game(self):
        reply = self.main_window_ref.show_message_box("Confirmar exclusão", f"Tem certeza que deseja excluir '{self.game['name']}'?", "question", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.game_manager.delete_game(self.game); self.main_window_ref.refresh_views(); self.accept()