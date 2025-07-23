# gui/list_item_widget.py

import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSignal

class GameListItemWidget(QWidget):
    details_clicked = pyqtSignal()
    play_clicked = pyqtSignal()

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)
        self.setAutoFillBackground(True)

        # Usando um QFrame como o container principal para garantir o estilo
        self.setObjectName("gameListItem")
        self.setStyleSheet("""
            #gameListItem {
                background-color: #2e2e2e;
                border: 1px solid #3a3d40;
                border-radius: 8px;
            }
            #gameListItem:hover {
                border-color: #4a90e2;
            }
        """)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Imagem
        image_label = QLabel()
        image_label.setFixedSize(140, 80)
        image_label.setStyleSheet("background-color: #1e1e1e; border-radius: 4px;")
        image_label.setAlignment(Qt.AlignCenter)
        
        image_path = self.game.get("background") or self.game.get("image")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(image_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("Sem Arte"); image_label.setStyleSheet("...; color: #888;")
        main_layout.addWidget(image_label)

        # Informações
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 5, 0, 5)
        name_label = QLabel(self.game["name"]); name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; background: transparent;")
        
        playtime_seconds = self.game.get("total_playtime", 0)
        playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas"); playtime_label.setStyleSheet("font-size: 13px; color: #ccc; background: transparent;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(playtime_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        # Botão Jogar
        self.play_btn = QPushButton("▶ Jogar")
        self.play_btn.setFixedSize(100, 40)
        self.play_btn.setStyleSheet("""
            QPushButton { background-color: #2c9a48; color: white; font-size: 14px; font-weight: bold; border-radius: 5px; } 
            QPushButton:hover { background-color: #36b558; }
        """)
        self.play_btn.clicked.connect(self.play_clicked.emit)
        main_layout.addWidget(self.play_btn)

    # MÉTODO DE CAPTURA DE CLIQUE SIMPLIFICADO
    def mousePressEvent(self, event):
        # Se o clique não foi no botão de jogar, emite o sinal de detalhes
        if not self.play_btn.geometry().contains(event.pos()):
            if event.button() == Qt.LeftButton:
                self.details_clicked.emit()
        # Passa o evento para o QWidget pai para outros processamentos (ex: arrastar)
        super().mousePressEvent(event)