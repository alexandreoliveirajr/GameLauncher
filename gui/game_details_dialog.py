# gui/game_details_dialog.py

import os
from datetime import datetime
from PyQt5.QtWidgets import (
   QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
   QMessageBox, QComboBox, QLineEdit, QFormLayout, QGroupBox,
   QInputDialog, QFileDialog, QGridLayout, QWidget,
   QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint

from core import steam_api

class GameDetailsDialog(QDialog):
    def __init__(self, game, game_manager, game_launcher, main_window_ref, parent=None):
        super().__init__(parent)
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
            painter.fillRect(self.rect(), QBrush(QColor("#1e1e1e")))
    
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        # MODIFICADO: Aumentando a transparência (de 0.75 para 0.65)
        overlay_panel = QWidget()
        overlay_panel.setStyleSheet("background-color: rgba(20, 20, 22, 0.65);")
        self.main_layout.addWidget(overlay_panel)

        panel_layout = QHBoxLayout(overlay_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        panel_layout.setSpacing(30)

        # --- Coluna da Esquerda (Capa do Jogo) ---
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
        
        # --- Coluna da Direita (Informações e Ações) ---
        right_column_layout = QVBoxLayout()
        panel_layout.addLayout(right_column_layout, 1)

        right_column_layout.addStretch(1)

        name_label = QLabel(self.game["name"])
        name_label.setStyleSheet("font-size: 34px; font-weight: bold; color: white;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        right_column_layout.addWidget(name_label)
        
        total_seconds = self.game.get("total_playtime", 0)
        playtime_str = self._format_playtime(total_seconds)
        playtime_label = QLabel(f"🕒 {playtime_str}")
        playtime_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ccc; margin-top: 10px;")
        playtime_label.setAlignment(Qt.AlignCenter)
        right_column_layout.addWidget(playtime_label)

        right_column_layout.addStretch(1)

        paths = self.game.get("paths", [])
        if len(paths) > 1:
            self.exec_combo = QComboBox()
            self.exec_combo.setStyleSheet("QComboBox { background-color: #333; color: white; padding: 8px; border-radius: 5px; }")
            for d in paths:
                self.exec_combo.addItem(d.get("display_name", os.path.basename(d["path"])), userData=d["path"])
            right_column_layout.addWidget(self.exec_combo)

        btn_play = QPushButton("▶ Jogar")
        btn_play.setStyleSheet("padding: 12px; font-size: 16px; font-weight: bold; background-color: #2c9a48; color: white; border-radius: 5px;")
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
        btn_fav = QPushButton(fav_text)
        btn_fav.setStyleSheet(button_style)
        btn_fav.clicked.connect(self._toggle_favorite)
        
        btn_edit = QPushButton("✏️ Editar")
        btn_edit.setStyleSheet(button_style)
        btn_edit.clicked.connect(self._edit_game_dialog)
        
        btn_delete = QPushButton("🗑️ Excluir")
        btn_delete.setStyleSheet(button_style)
        btn_delete.clicked.connect(self._delete_game)

        action_buttons_layout.addWidget(btn_fav)
        action_buttons_layout.addWidget(btn_edit)
        action_buttons_layout.addWidget(btn_delete)
        right_column_layout.addLayout(action_buttons_layout)

        bg_path = self.game.get("background")
        if bg_path and os.path.exists(bg_path):
            self.background_pixmap = QPixmap(bg_path)
            
    def _format_playtime(self, total_seconds):
        if total_seconds <= 0: return "Nenhum tempo registrado"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0 and minutes > 0: return f"{hours}h e {minutes}min"
        elif hours > 0: return f"{hours}h"
        elif minutes > 0: return f"{minutes}min"
        else: return "Menos de 1 minuto"

    def _launch_selected_game(self):
        selected_path = self.exec_combo.currentData()
        self._launch_game(selected_path)

    def _launch_game(self, path):
        result, data = self.game_launcher.launch_game(self.game, path)
        if result == "running": self.main_window_ref.show_message_box("Jogo em execução", f"O jogo '{os.path.basename(path)}' já está em execução.", "info")
        elif result == "error": self.main_window_ref.show_message_box("Erro ao abrir", f"Não foi possível abrir o jogo:\n{data}", "warning")
        else:
            process, game = result, data
            self.main_window_ref.start_tracking_game(process, game)
            self.main_window_ref.refresh_views()
            self.accept()

    def _toggle_favorite(self):
        self.game_manager.toggle_favorite(self.game)
        self.main_window_ref.refresh_views()
        self.accept()
        
    def _edit_game_dialog(self):
        edit_dialog = QDialog(self)
        edit_dialog.setWindowTitle(f"Editar {self.current_edited_game['name']}")
        edit_dialog.setStyleSheet("background-color: #1e1e1e; color: white;")
        edit_layout = QFormLayout()

        name_input = QLineEdit(self.current_edited_game["name"])
        edit_layout.addRow("Nome:", name_input)

        fetch_art_btn = QPushButton("🔎 Buscar Arte na Steam por Nome")
        fetch_art_btn.setStyleSheet("background-color: #1b2838; color: white; padding: 8px;")
        # Passamos os widgets que precisam ser atualizados para a função
        fetch_art_btn.clicked.connect(
            lambda: self._fetch_steam_artwork(
                name_input.text(), 
                self.img_btn_ref,  # Precisamos de uma referência para os botões
                self.bg_btn_ref
            )
        )
        edit_layout.addRow(fetch_art_btn)

        paths_group_box = QGroupBox("Executáveis"); 
        paths_group_box.setStyleSheet("color: white;"); self.paths_edit_layout = QVBoxLayout(); paths_group_box.setLayout(self.paths_edit_layout); edit_layout.addRow(paths_group_box); self._refresh_edit_paths_labels()
        btn_add_path = QPushButton("Adicionar Executável"); btn_add_path.clicked.connect(self._edit_add_path); edit_layout.addRow(btn_add_path)
        btn_remove_path = QPushButton("Remover Selecionado"); btn_remove_path.clicked.connect(self._edit_remove_path); edit_layout.addRow(btn_remove_path)
        
        img_path = self.current_edited_game.get('image'); img_text = os.path.basename(img_path) if img_path else 'Nenhuma selecionada'
        self.img_btn_ref = QPushButton(f"Alterar imagem ({img_text})") # Salva a referência
        self.img_btn_ref.clicked.connect(self._edit_change_image); edit_layout.addRow(self.img_btn_ref)

        bg_path = self.current_edited_game.get('background'); bg_text = os.path.basename(bg_path) if bg_path else 'Nenhuma selecionada'
        self.bg_btn_ref = QPushButton(f"Alterar imagem de fundo ({bg_text})") # Salva a referência
        self.bg_btn_ref.clicked.connect(self._edit_change_background); edit_layout.addRow(self.bg_btn_ref)
        
        btn_save = QPushButton("Salvar Alterações"); btn_save.setStyleSheet("background-color: #3c3; color: black; font-weight: bold;"); btn_save.clicked.connect(lambda: self._save_edited_game(name_input.text(), edit_dialog)); edit_layout.addRow(btn_save)
        edit_dialog.setLayout(edit_layout);
        if edit_dialog.exec_(): self.main_window_ref.refresh_views(); self.accept()

    def _fetch_steam_artwork(self, game_name, img_button_ref, bg_button_ref):
        app_id = steam_api.find_appid_by_name(game_name)
        if not app_id:
            self.main_window_ref.show_message_box("Não encontrado", f"Não foi possível encontrar um jogo correspondente a '{game_name}' na lista de apps da Steam. Tente ajustar o nome.", "warning")
            return

        artwork = steam_api.download_steam_artwork(app_id)
        if not artwork:
            self.main_window_ref.show_message_box("Sem Arte", f"Jogo encontrado (AppID: {app_id}), mas não foi possível baixar a arte.", "warning")
            return
            
        # Atualiza os dados em memória
        new_image_path = artwork.get("image")
        if new_image_path:
            self.current_edited_game["image"] = new_image_path
            img_button_ref.setText(f"Alterar imagem ({os.path.basename(new_image_path)})")
            
        new_bg_path = artwork.get("background")
        if new_bg_path:
            self.current_edited_game["background"] = new_bg_path
            bg_button_ref.setText(f"Alterar imagem de fundo ({os.path.basename(new_bg_path)})")

        self.main_window_ref.show_message_box("Sucesso", "Arte da Steam baixada e aplicada! Clique em 'Salvar Alterações' para confirmar.", "info")

    def _refresh_edit_paths_labels(self):
        for i in reversed(range(self.paths_edit_layout.count())):
            widget = self.paths_edit_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if self.current_edited_game.get("paths"):
            for d in self.current_edited_game["paths"]:
                lbl = QLabel(f"• {d.get('display_name', '')} — {os.path.basename(d['path'])}")
                lbl.setStyleSheet("color: white;")
                lbl.setWordWrap(True)
                self.paths_edit_layout.addWidget(lbl)
        else:
            lbl = QLabel("(Nenhum executável adicionado)")
            lbl.setStyleSheet("color: #777; font-style: italic;")
            self.paths_edit_layout.addWidget(lbl)
    
    def _edit_add_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar executável")
        if file_path:
            name, ok = QInputDialog.getText(self, "Nome de Exibição", "Digite um nome para este executável:", QLineEdit.Normal, os.path.basename(file_path))
            if ok and name.strip():
                if not any(d['path'] == file_path for d in self.current_edited_game["paths"]):
                    self.current_edited_game["paths"].append({"path": file_path, "display_name": name.strip()})
                    self._refresh_edit_paths_labels()

    def _edit_remove_path(self):
        if not self.current_edited_game.get("paths"):
            self.main_window_ref.show_message_box("Erro", "Não há executáveis para remover.", "warning")
            return
        items = [f"{d.get('display_name', '')} - {os.path.basename(d['path'])}" for d in self.current_edited_game["paths"]]
        item, ok = QInputDialog.getItem(self, "Remover Executável", "Selecione o executável para remover:", items, 0, False)
        if ok and item:
            for idx, d in enumerate(self.current_edited_game["paths"]):
                if f"{d.get('display_name', '')} - {os.path.basename(d['path'])}" == item:
                    del self.current_edited_game["paths"][idx]
                    break
            self._refresh_edit_paths_labels()

    def _edit_change_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar imagem", filter="Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:
            self.current_edited_game["image"] = file_path
            sender_button = self.sender()
            if sender_button:
                sender_button.setText(f"Alterar imagem ({os.path.basename(file_path)})")

    def _edit_change_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar imagem de fundo", filter="Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file_path:
            self.current_edited_game["background"] = file_path
            sender_button = self.sender()
            if sender_button:
                sender_button.setText(f"Alterar imagem de fundo ({os.path.basename(file_path)})")

    def _save_edited_game(self, new_name, dialog):
        new_name = new_name.strip()
        if not new_name or not self.current_edited_game["paths"]:
            self.main_window_ref.show_message_box("Erro", "Nome e ao menos um executável são obrigatórios.", "warning")
            return
        self.current_edited_game["name"] = new_name
        self.game_manager.update_game(self.original_game_state, self.current_edited_game)
        dialog.accept()

    def _delete_game(self):
        reply = self.main_window_ref.show_message_box("Confirmar exclusão", f"Tem certeza que deseja excluir '{self.game['name']}'?", "question", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.game_manager.delete_game(self.game)
            self.main_window_ref.refresh_views()
            self.accept()