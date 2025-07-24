# gui/edit_profile_dialog.py

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QHBoxLayout, QSpacerItem, QSizePolicy,
    QComboBox
)
from core.theme import current_theme

class EditProfileDialog(QDialog):
    def __init__(self, profile_manager, game_manager, parent=None):
        super().__init__(parent)
        # Pega as "flags" (configurações) atuais da janela
        flags = self.windowFlags()
        # Remove APENAS a flag do botão de ajuda, mantendo todas as outras
        self.setWindowFlags(flags & ~Qt.WindowContextHelpButtonHint)
        self.profile_manager = profile_manager
        self.game_manager = game_manager # Precisamos para listar os favoritos
        self.current_data = self.profile_manager.get_data().copy()

        self.new_avatar_path = self.current_data.get("avatar_path")
        self.new_background_path = self.current_data.get("background_path")

        self.setWindowTitle("Editar Perfil")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"""
            QDialog {{ 
                background-color: {current_theme['background'].name()}; 
                color: {current_theme['text_primary'].name()}; 
            }}
            QLineEdit, QTextEdit, QComboBox {{ 
                background-color: {current_theme['button_options'].name()}; 
                border: 1px solid {current_theme['button_neutral'].name()}; 
                border-radius: 5px; padding: 8px; 
                color: {current_theme['text_primary'].name()};
            }}
            QPushButton {{ 
                padding: 10px 15px; font-size: 14px; border-radius: 8px;
                background-color: {current_theme['button_neutral'].name()};
            }}
            QPushButton#saveButton {{
                background-color: {current_theme['accent_success_bright'].name()}; 
                color: {current_theme['text_inverted'].name()}; 
                font-weight: bold;
            }}
        """)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_input = QLineEdit(self.current_data.get("username", ""))
        form_layout.addRow("Nome de Usuário:", self.username_input)

        self.bio_input = QTextEdit(self.current_data.get("bio", ""))
        self.bio_input.setMaximumHeight(100)
        form_layout.addRow("Bio:", self.bio_input)

        avatar_text = os.path.basename(self.new_avatar_path) if self.new_avatar_path else "Nenhum"
        self.avatar_btn = QPushButton(f"Avatar: {avatar_text}")
        self.avatar_btn.clicked.connect(self._select_avatar)
        form_layout.addRow("Alterar Avatar:", self.avatar_btn)
        
        bg_text = os.path.basename(self.new_background_path) if self.new_background_path else "Nenhum"
        self.background_btn = QPushButton(f"Fundo: {bg_text}")
        self.background_btn.clicked.connect(self._select_background)
        form_layout.addRow("Alterar Fundo do Perfil:", self.background_btn)

        # ADICIONADO: ComboBox para selecionar o jogo favorito em destaque
        self.favorite_combo = QComboBox()
        self.populate_favorites_combo()
        form_layout.addRow("Jogo Favorito em Destaque:", self.favorite_combo)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        cancel_button = QPushButton("Cancelar"); cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        save_button = QPushButton("Salvar Alterações"); save_button.setObjectName("saveButton"); save_button.clicked.connect(self._save_changes)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

    def populate_favorites_combo(self):
        self.favorite_combo.addItem("Nenhum", None) # Opção para não exibir nenhum
        
        favorite_games = self.game_manager.get_favorite_games()
        current_favorite_id = self.current_data.get("showcased_favorite_id")
        
        for i, game in enumerate(favorite_games):
            self.favorite_combo.addItem(game['name'], game['id'])
            if game['id'] == current_favorite_id:
                self.favorite_combo.setCurrentIndex(i + 1)

    def _select_avatar(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Avatar", "", "Imagens (*.png *.jpg *.jpeg *.gif)")
        if file_path:
            self.new_avatar_path = file_path
            self.avatar_btn.setText(f"Avatar: {os.path.basename(file_path)}")

    def _select_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem de Fundo", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.new_background_path = file_path
            self.background_btn.setText(f"Fundo: {os.path.basename(file_path)}")

    def _save_changes(self):
        self.current_data["username"] = self.username_input.text()
        self.current_data["bio"] = self.bio_input.toPlainText()
        self.current_data["avatar_path"] = self.new_avatar_path
        self.current_data["background_path"] = self.new_background_path
        # Salva a ID do jogo selecionado no ComboBox
        self.current_data["showcased_favorite_id"] = self.favorite_combo.currentData()

        self.profile_manager.save_profile(self.current_data)
        self.accept()