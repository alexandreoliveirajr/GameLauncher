# gui/animated_card.py

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QColor, QPainter
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve, Qt
from core.theme import current_theme

class AnimatedGameCard(QPushButton):
    def __init__(self, game, title="", card_size=(200, 220), mode='vertical', parent=None):
        super().__init__(parent)
        self.game = game
        self.title = title # Armazena o título
        self.card_size = card_size
        self.mode = mode

        self.setFixedSize(*self.card_size)
        self._setup_ui()
        self._setup_animation()
        self._setup_shadow()

    def _setup_ui(self):
        if self.mode == 'vertical':
            self._setup_vertical_layout()
        else:
            self._setup_horizontal_layout()
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {current_theme['card'].name()};
                color: {current_theme['text_primary'].name()};
                border: 1px solid {current_theme['card_border'].name()};
                border-radius: 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                border: 1px solid {current_theme['accent'].name()};
            }}
        """)

    def _setup_vertical_layout(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(5)
        image_label = QLabel()
        if self.game and self.game.get("image") and os.path.exists(self.game["image"]):
            pixmap = QPixmap(self.game["image"]).scaled(self.card_size[0] - 20, self.card_size[1] - 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            placeholder_pixmap = QPixmap(self.card_size[0] - 20, self.card_size[1] - 50); placeholder_pixmap.fill(QColor("#333"))
            painter = QPainter(placeholder_pixmap)
            painter.setPen(QColor(current_theme['text_primary'])); painter.drawText(placeholder_pixmap.rect(), Qt.AlignCenter, "Sem Imagem"); painter.end()
            image_label.setPixmap(placeholder_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        name_label = QLabel(self.game["name"]); name_label.setStyleSheet("background: transparent; border: none; color: white; font-weight: bold;"); name_label.setAlignment(Qt.AlignCenter); name_label.setWordWrap(True)
        layout.addWidget(name_label)

    def _setup_horizontal_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        image_label = QLabel()
        image_label.setFixedSize(220, 160)
        image_label.setStyleSheet("background: #1e1e1e; border-radius: 8px; border: none;")
        main_layout.addWidget(image_label)
        
        image_to_display = self.game.get("header_path") or self.game.get("image")

        if self.game and image_to_display and os.path.exists(image_to_display):
            pixmap = QPixmap(image_to_display).scaled(image_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            
        info_layout = QVBoxLayout(); info_layout.setContentsMargins(5, 5, 5, 5)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {current_theme['accent'].name()}; background: transparent; border: none;")
        
        name_label = QLabel(self.game["name"]); name_label.setStyleSheet("font-size: 24px; font-weight: bold; background: transparent; color: white; border: none;"); name_label.setWordWrap(True)
        playtime_seconds = self.game.get("total_playtime", 0); playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas"); playtime_label.setStyleSheet("font-size: 16px; color: #ccc; background: transparent; border: none;")
        info_layout.addWidget(title_label); info_layout.addWidget(name_label); info_layout.addStretch(); info_layout.addWidget(playtime_label)
        main_layout.addLayout(info_layout, 1)

    # O resto da classe (animação, sombra, eventos) permanece o mesmo
    def _setup_shadow(self):
        self.shadow = QGraphicsDropShadowEffect(self); self.shadow.setBlurRadius(25); self.shadow.setXOffset(0); self.shadow.setYOffset(5); self.shadow.setColor(QColor(0, 0, 0, 160)); self.setGraphicsEffect(self.shadow)
    def _setup_animation(self):
        self.enter_animation = QPropertyAnimation(self, b"geometry"); self.enter_animation.setDuration(150); self.enter_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.leave_animation = QPropertyAnimation(self, b"geometry"); self.leave_animation.setDuration(150); self.leave_animation.setEasingCurve(QEasingCurve.OutQuad)
    def enterEvent(self, event):
        current_geo = self.geometry(); start_geo = QRect(current_geo.x(), current_geo.y(), self.width(), self.height()); end_geo = QRect(current_geo.x() - 5, current_geo.y() - 5, self.width() + 10, self.height() + 10)
        self.enter_animation.setStartValue(start_geo); self.enter_animation.setEndValue(end_geo); self.leave_animation.stop(); self.enter_animation.start(); self.raise_(); super().enterEvent(event)
    def leaveEvent(self, event):
        start_geo = self.geometry(); end_geo = QRect(start_geo.x() + 5, start_geo.y() + 5, self.width() - 10, self.height() - 10)
        self.leave_animation.setStartValue(start_geo); self.leave_animation.setEndValue(end_geo); self.enter_animation.stop(); self.leave_animation.start(); super().leaveEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.shadow.setBlurRadius(15); self.shadow.setYOffset(2)
        super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.shadow.setBlurRadius(25); self.shadow.setYOffset(5)
        super().mouseReleaseEvent(event)