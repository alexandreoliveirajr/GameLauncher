# gui/metadata_review_dialog.py

import os
import requests
import logging # Adicionado para um logging mais claro
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QScrollArea, QWidget, QFrame, QCheckBox, QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# Precisamos do diálogo de busca do IGDB aqui
from gui.igdb_search_dialog import IGDBSearchDialog

class MetadataSuggestionWidget(QFrame):
    """
    Widget customizado para exibir uma sugestão, agora com um botão para alterar a seleção.
    """
    change_requested = pyqtSignal(object) 

    def __init__(self, suggestion_data, parent=None):
        super().__init__(parent)
        self.suggestion_data = suggestion_data
        self.setObjectName("SuggestionCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._setup_ui()
        self.load_artwork_preview()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        self.artwork_label = QLabel("A carregar...")
        self.artwork_label.setFixedSize(60, 90)
        self.artwork_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artwork_label.setStyleSheet("background-color: #2a2a2e; border-radius: 4px;")

        info_layout = QVBoxLayout()
        self.game_name_label = QLabel(f"<b>O seu Jogo:</b> {self.suggestion_data['original_name']}")
        self.suggestion_label = QLabel(f"<b>Sugestão:</b> {self.suggestion_data['suggestion_name']}")
        self.source_label = QLabel(f"<b>Fonte:</b> {self.suggestion_data['source'].upper()}")
        
        info_layout.addWidget(self.game_name_label)
        info_layout.addWidget(self.suggestion_label)
        info_layout.addWidget(self.source_label)
        info_layout.addStretch()

        action_layout = QVBoxLayout()
        self.approve_checkbox = QCheckBox("Aprovar")
        self.approve_checkbox.setChecked(True)
        
        self.change_button = QPushButton("Alterar")
        self.change_button.clicked.connect(lambda: self.change_requested.emit(self))
        self.change_button.setVisible(True)

        action_layout.addWidget(self.approve_checkbox)
        action_layout.addWidget(self.change_button)
        action_layout.addStretch()

        main_layout.addWidget(self.artwork_label)
        main_layout.addLayout(info_layout, 1)
        main_layout.addLayout(action_layout)

    def update_suggestion(self, new_igdb_data):
        """Atualiza o widget com uma nova sugestão do IGDB."""
        self.suggestion_data['suggestion_name'] = new_igdb_data.get('name', 'N/A')
        self.suggestion_data['igdb_data'] = new_igdb_data
        
        self.suggestion_data['source'] = 'igdb'
        self.suggestion_data.pop('appid', None)

        preview_url = new_igdb_data.get('cover_url', '')
        if preview_url:
            preview_url = preview_url.replace('t_thumb', 't_cover_big')
        self.suggestion_data['preview_url'] = preview_url

        self.suggestion_label.setText(f"<b>Sugestão:</b> {self.suggestion_data['suggestion_name']}")
        self.source_label.setText(f"<b>Fonte:</b> {self.suggestion_data['source'].upper()}")
        self.load_artwork_preview()

    def load_artwork_preview(self):
        """Baixa a imagem de preview e a exibe diretamente da memória."""
        preview_url = self.suggestion_data.get('preview_url')
        if not preview_url:
            self.artwork_label.setText("Sem Arte")
            return

        try:
            full_url = f"https:{preview_url}" if preview_url.startswith("//") else preview_url
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            
            response = requests.get(full_url, headers=headers, stream=True, timeout=15)
            
            if response.status_code == 200:
                image_data = response.content
                pixmap = QPixmap()
                
                # --- INÍCIO DO DIAGNÓSTICO ---
                # Tentamos carregar os dados e capturamos qualquer erro
                load_successful = pixmap.loadFromData(image_data)
                
                if not load_successful:
                    logging.error("Falha ao carregar a imagem a partir dos dados. Os dados podem estar corrompidos ou num formato não suportado.")
                    self.artwork_label.setText("Inválida")
                    return
                # --- FIM DO DIAGNÓSTICO ---

                self.artwork_label.setPixmap(pixmap.scaled(
                    self.artwork_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                logging.warning(f"Falha ao baixar a imagem de preview de {full_url}. Status: {response.status_code}")
                self.artwork_label.setText(f"Erro {response.status_code}")
                return

        except Exception as e:
            # Captura e exibe o erro completo no terminal
            logging.error(f"Ocorreu uma exceção ao carregar a imagem de preview: {e}", exc_info=True)
            self.artwork_label.setText("Falha")

    def is_approved(self):
        return self.approve_checkbox.isChecked()


class MetadataReviewDialog(QDialog):
    def __init__(self, suggestions, igdb_api, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rever Metadados Encontrados")
        self.setMinimumSize(700, 500)
        self.suggestions = suggestions
        self.igdb_api = igdb_api
        self.suggestion_widgets = []

        main_layout = QVBoxLayout(self)
        title_label = QLabel("Encontrámos as seguintes sugestões. Desmarque ou altere as que não estiverem corretas.")
        main_layout.addWidget(title_label)

        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setObjectName("ReviewScrollArea")
        container_widget = QWidget()
        self.list_layout = QVBoxLayout(container_widget)
        self.list_layout.setSpacing(10)
        scroll_area.setWidget(container_widget)
        main_layout.addWidget(scroll_area)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_button = QPushButton("Cancelar"); self.cancel_button.clicked.connect(self.reject)
        self.apply_button = QPushButton("Aplicar Selecionados"); self.apply_button.setObjectName("AcceptButton"); self.apply_button.clicked.connect(self.accept)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)
        main_layout.addLayout(button_layout)

        self.populate_suggestions()

    def populate_suggestions(self):
        if not self.suggestions:
            self.list_layout.addWidget(QLabel("Nenhuma sugestão nova encontrada."))
        
        for suggestion in self.suggestions:
            widget = MetadataSuggestionWidget(suggestion)
            widget.change_requested.connect(self.handle_change_request)
            self.suggestion_widgets.append(widget)
            self.list_layout.addWidget(widget)
        
        self.list_layout.addStretch()

    def handle_change_request(self, suggestion_widget):
        """Chamado quando o utilizador clica em 'Alterar' numa sugestão."""
        original_name = suggestion_widget.suggestion_data['original_name']
        
        results = self.igdb_api.search_games(original_name)
        if not results:
            QMessageBox.information(self, "Busca", "Nenhum outro resultado encontrado no IGDB.")
            return

        search_dialog = IGDBSearchDialog(results, self)
        if search_dialog.exec():
            new_selection = search_dialog.get_selected_game()
            if new_selection:
                suggestion_widget.update_suggestion(new_selection)

    def get_approved_suggestions(self):
        approved = []
        for widget in self.suggestion_widgets:
            if widget.is_approved():
                approved.append(widget.suggestion_data)
        return approved
