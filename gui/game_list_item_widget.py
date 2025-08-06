# gui/game_list_item_widget.py

import os
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsColorizeEffect
from PyQt6.QtGui import QPixmap, QColor, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QPropertyAnimation, QRect, QEasingCurve

class GameListItemWidget(QFrame):
    details_clicked = pyqtSignal()
    play_clicked = pyqtSignal()

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.setObjectName("GameListItem")
        self.game = game
        self.setFixedHeight(100)
        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 20, 10)
        main_layout.setSpacing(15)

        self.image_label = QLabel()
        self.image_label.setObjectName("GameListItemImage")
        self.image_label.setFixedSize(160, 75)
        
        # --- INÍCIO DA ALTERAÇÃO ---
        # Usa header_path como prioridade, depois image_path
        image_path = self.game.get("header_path") or self.game.get("image_path")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Sem Arte")
        
        # Aplica o efeito de "cinza" se o jogo não estiver instalado
        self._apply_status_effect()
        # --- FIM DA ALTERAÇÃO ---

        main_layout.addWidget(self.image_label)

        info_layout = QVBoxLayout()
        name_label = QLabel(self.game["name"])
        name_label.setObjectName("GameListItemName")
        
        playtime_seconds = self.game.get("playtime_local", 0)
        playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas")
        playtime_label.setObjectName("GameListItemPlaytime")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(playtime_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        self.play_btn = QPushButton()
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.setFixedSize(120, 45)
        self.play_btn.clicked.connect(self.play_clicked.emit)
        
        # --- INÍCIO DA ALTERAÇÃO ---
        # Muda o texto e o ícone do botão com base no status
        is_installed = self.game.get("status", "UNINSTALLED") == "INSTALLED"
        if is_installed:
            self.play_btn.setText(" Jogar")
            self.play_btn.setIcon(QIcon("assets/icons/play.svg"))
            self.play_btn.setIconSize(QSize(16, 16))
        else:
            self.play_btn.setText(" Instalar")
            self.play_btn.setIcon(QIcon("assets/icons/download.svg"))
            self.play_btn.setIconSize(QSize(18, 18))
        # --- FIM DA ALTERAÇÃO ---
        
        main_layout.addWidget(self.play_btn)

    def _apply_status_effect(self):
        """Aplica um efeito de escala de cinza se o jogo não estiver instalado."""
        is_installed = self.game.get("status", "UNINSTALLED") == "INSTALLED"
        if not is_installed:
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor(128, 128, 128))
            effect.setStrength(0.8)
            self.image_label.setGraphicsEffect(effect)
        else:
            self.image_label.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        play_button = self.findChild(QPushButton, "PlayButton")
        if not play_button or not play_button.geometry().contains(event.pos()):
            if event.button() == Qt.MouseButton.LeftButton:
                self.details_clicked.emit()
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
