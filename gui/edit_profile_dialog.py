# gui/edit_profile_dialog.py

import os
import pycountry
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QHBoxLayout, QSpacerItem, QSizePolicy,
    QComboBox
)

class EditProfileDialog(QDialog):
    def __init__(self, profile_manager, game_manager, parent=None):
        super().__init__(parent)
        flags = self.windowFlags()
        self.setWindowFlags(flags & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.profile_manager = profile_manager
        self.game_manager = game_manager
        self.current_data = self.profile_manager.get_data().copy()

        self.new_avatar_path = self.current_data.get("avatar_path")
        self.new_background_path = self.current_data.get("background_path")

        self.setWindowTitle("Editar Perfil")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_input = QLineEdit(self.current_data.get("username", ""))
        form_layout.addRow("Nome de Usuário:", self.username_input)

        # --- NOVO CAMPO: Nome Verdadeiro ---
        self.real_name_input = QLineEdit(self.current_data.get("real_name", ""))
        self.real_name_input.setPlaceholderText("Opcional")
        form_layout.addRow("Nome Verdadeiro:", self.real_name_input)

        self.bio_input = QTextEdit(self.current_data.get("bio", ""))
        self.bio_input.setMaximumHeight(100)
        form_layout.addRow("Bio:", self.bio_input)
        
        # --- NOVO CAMPO: País ---
        self.country_combo = QComboBox()
        self.populate_countries_combo()
        form_layout.addRow("País:", self.country_combo)

        avatar_text = os.path.basename(self.new_avatar_path) if self.new_avatar_path else "Nenhum"
        self.avatar_btn = QPushButton(f"Avatar: {avatar_text}")
        self.avatar_btn.clicked.connect(self._select_avatar)
        form_layout.addRow("Alterar Avatar:", self.avatar_btn)
        
        bg_text = os.path.basename(self.new_background_path) if self.new_background_path else "Nenhum"
        self.background_btn = QPushButton(f"Fundo: {bg_text}")
        self.background_btn.clicked.connect(self._select_background)
        form_layout.addRow("Alterar Fundo do Perfil:", self.background_btn)

        self.favorite_combo = QComboBox()
        self.populate_favorites_combo()
        form_layout.addRow("Jogo Favorito em Destaque:", self.favorite_combo)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        cancel_button = QPushButton("Cancelar"); cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        save_button = QPushButton("Salvar Alterações"); save_button.setObjectName("saveButton"); save_button.clicked.connect(self._save_changes)
        button_layout.addWidget(save_button)
        main_layout.addLayout(button_layout)

    def populate_countries_combo(self):
        """Popula o ComboBox com uma lista de países e seleciona o atual."""
        self.country_combo.addItem("Não especificado", None) # Opção padrão
        
        # Gera uma lista de tuplas (Nome do País, Código do País)
        countries = sorted([(country.name, country.alpha_2) for country in pycountry.countries])
        
        current_code = self.current_data.get("country_code")
        
        for i, (name, code) in enumerate(countries):
            self.country_combo.addItem(name, code)
            if code == current_code:
                self.country_combo.setCurrentIndex(i + 1)

    def populate_favorites_combo(self):
        # ... (este método continua igual)
        self.favorite_combo.addItem("Nenhum", None)
        favorite_games = self.game_manager.get_favorite_games()
        current_favorite_id = self.current_data.get("showcased_favorite_id")
        for i, game in enumerate(favorite_games):
            self.favorite_combo.addItem(game['name'], game['id'])
            if game['id'] == current_favorite_id:
                self.favorite_combo.setCurrentIndex(i + 1)

    def _select_avatar(self):
        # ... (este método continua igual)
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Avatar", "", "Imagens (*.png *.jpg *.jpeg *.gif)")
        if file_path:
            self.new_avatar_path = file_path
            self.avatar_btn.setText(f"Avatar: {os.path.basename(file_path)}")

    def _select_background(self):
        # ... (este método continua igual)
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem de Fundo", "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.new_background_path = file_path
            self.background_btn.setText(f"Fundo: {os.path.basename(file_path)}")

    def _save_changes(self):
        self.current_data["username"] = self.username_input.text()
        self.current_data["real_name"] = self.real_name_input.text() # SALVA O NOVO CAMPO
        self.current_data["country_code"] = self.country_combo.currentData() # SALVA O NOVO CAMPO
        self.current_data["bio"] = self.bio_input.toPlainText()
        self.current_data["avatar_path"] = self.new_avatar_path
        self.current_data["background_path"] = self.new_background_path
        self.current_data["showcased_favorite_id"] = self.favorite_combo.currentData()

        self.profile_manager.save_profile(self.current_data)
        self.accept()