# gui/game_list_item_widget.py (VERSÃO APRIMORADA)

import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPixmap, QColor, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPropertyAnimation, QRect, QEasingCurve

class GameListItemWidget(QFrame):
    details_clicked = pyqtSignal() # Sinal para abrir detalhes
    play_clicked = pyqtSignal()    # Sinal para jogar

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.setObjectName("GameListItem")
        self.game = game
        self.setFixedHeight(100) # Altura fixa para o item da lista
        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 20, 10)
        main_layout.setSpacing(15)

        # --- Imagem Retangular (CORRIGIDO) ---
        image_label = QLabel()
        image_label.setObjectName("GameListItemImage")
        image_label.setFixedSize(160, 75) # 1. Voltamos para um tamanho retangular
        
        image_path = self.game.get("header_path") or self.game.get("image")
        if image_path and os.path.exists(image_path):
            # 2. Voltamos para KeepAspectRatioByExpanding para preencher o espaço
            pixmap = QPixmap(image_path).scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Sem Arte")
        main_layout.addWidget(image_label)

        # --- O resto do método continua igual ---
        info_layout = QVBoxLayout()
        name_label = QLabel(self.game["name"])
        name_label.setObjectName("GameListItemName")
        
        playtime_seconds = self.game.get("total_playtime", 0)
        playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas")
        playtime_label.setObjectName("GameListItemPlaytime")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(playtime_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        play_btn = QPushButton(" Jogar")
        play_btn.setObjectName("PlayButton")
        play_btn.setIcon(QIcon("assets/icons/play.svg"))
        play_btn.setIconSize(QSize(16, 16))
        play_btn.setFixedSize(120, 45)
        play_btn.clicked.connect(self.play_clicked.emit)
        main_layout.addWidget(play_btn)

    def mousePressEvent(self, event):
        # Verifica se o clique foi fora do botão "Jogar"
        play_button = self.findChild(QPushButton, "PlayButton")
        if not play_button or not play_button.geometry().contains(event.pos()):
            if event.button() == Qt.MouseButton.LeftButton:
                self.details_clicked.emit() # Emite o sinal de detalhes
        super().mousePressEvent(event)

    def _setup_animation(self):
        self.enter_animation = QPropertyAnimation(self, b"geometry")
        self.enter_animation.setDuration(150)
        self.enter_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.leave_animation = QPropertyAnimation(self, b"geometry")
        self.leave_animation.setDuration(150)
        self.leave_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        current_geo = self.geometry()
        end_geo = QRect(current_geo.x(), current_geo.y() - 2, self.width(), self.height() + 4)
        self.enter_animation.setStartValue(self.geometry())
        self.enter_animation.setEndValue(end_geo)
        self.leave_animation.stop()
        self.enter_animation.start()
        self.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event):
        start_geo = self.geometry()
        end_geo = QRect(start_geo.x(), start_geo.y() + 2, self.width(), self.height() - 4)
        self.leave_animation.setStartValue(start_geo)
        self.leave_animation.setEndValue(end_geo)
        self.enter_animation.stop()
        self.leave_animation.start()
        super().leaveEvent(event)