# gui/settings_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

class SettingsTab(QWidget):
    def __init__(self, profile_manager, main_window_ref, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.main_window_ref = main_window_ref # Guardamos a referência para mostrar mensagens

        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        # Adicionamos margens para que não fique colado às bordas da área de conteúdo
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título da página
        title_label = QLabel("Configurações")
        title_label.setObjectName("PageTitleLabel") # Pode estilizar isso no seu QSS
        main_layout.addWidget(title_label)

        # --- Seção de Contas Vinculadas ---
        steam_group_frame = QFrame()
        steam_group_frame.setObjectName("SettingsGroupFrame")
        steam_group_layout = QVBoxLayout(steam_group_frame)
        
        status_layout = QHBoxLayout()
        self.steam_status_label = QLabel("<b>Conta Steam:</b> Não vinculada")
        self.link_steam_btn = QPushButton("Vincular Conta")
        self.link_steam_btn.clicked.connect(self.toggle_steam_fields)
        status_layout.addWidget(self.steam_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.link_steam_btn)
        
        self.steam_fields_container = QWidget()
        form_layout = QFormLayout(self.steam_fields_container)
        form_layout.setContentsMargins(0, 10, 0, 0)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Cole sua Chave de API da Web da Steam aqui")
        form_layout.addRow("Chave de API:", self.api_key_input)

        self.steam_id_input = QLineEdit()
        self.steam_id_input.setPlaceholderText("Cole seu SteamID64 aqui")
        form_layout.addRow("SteamID64:", self.steam_id_input)
        
        help_label = QLabel('<a href="https://steamcommunity.com/dev/apikey">Onde encontrar sua Chave de API</a> e <a href="https://steamid.io/">seu SteamID64</a>')
        help_label.setOpenExternalLinks(True)
        form_layout.addRow("", help_label)

        steam_group_layout.addLayout(status_layout)
        steam_group_layout.addWidget(self.steam_fields_container)

        # Botão de Salvar, agora dentro da própria aba
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        save_btn = QPushButton("Salvar Configurações")
        save_btn.setObjectName("AcceptButton") # Reutiliza o estilo do botão de aceitar
        save_btn.clicked.connect(self.save_settings)
        save_button_layout.addWidget(save_btn)

        main_layout.addWidget(steam_group_frame)
        main_layout.addStretch() # Empurra tudo para cima
        main_layout.addLayout(save_button_layout)

    def load_settings(self):
        """Carrega as configurações e ajusta a UI de acordo."""
        profile_data = self.profile_manager.get_data()
        api_key = profile_data.get('steam_api_key', '')
        steam_id = profile_data.get('steam_id_64', '')

        self.api_key_input.setText(api_key)
        self.steam_id_input.setText(steam_id)

        if api_key and steam_id:
            self.steam_status_label.setText("<b>Conta Steam:</b> Vinculada")
            self.link_steam_btn.setText("Gerenciar")
            self.steam_fields_container.hide()
        else:
            self.steam_status_label.setText("<b>Conta Steam:</b> Não vinculada")
            self.link_steam_btn.setText("Vincular Conta")
            self.steam_fields_container.show()

    def toggle_steam_fields(self):
        """Mostra ou esconde os campos de entrada da Steam."""
        if self.steam_fields_container.isVisible():
            self.steam_fields_container.hide()
        else:
            self.steam_fields_container.show()

    def save_settings(self):
        """Salva as configurações inseridas pelo usuário."""
        api_key = self.api_key_input.text().strip()
        steam_id = self.steam_id_input.text().strip()

        if (api_key and not steam_id) or (not api_key and steam_id):
            self.main_window_ref.show_message_box("Campos Incompletos", "Para a integração com a Steam funcionar, você precisa preencher tanto a Chave de API quanto o SteamID64.", "warning")
            return
        
        if not api_key and not steam_id:
            reply = self.main_window_ref.show_message_box("Desvincular Conta", 
                                         "Você tem certeza que deseja desvincular sua conta Steam?",
                                         "question", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        self.profile_manager.update_steam_credentials(api_key, steam_id)
        
        self.main_window_ref.show_message_box("Sucesso", "Configurações da Steam salvas com sucesso!", "info")
        # Recarrega as configurações para atualizar o status na tela
        self.load_settings()

