# gui/animated_card.py

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPixmap, QColor, QPainter, QAction
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, Qt

class AnimatedGameCard(QPushButton):
    def __init__(self, game, title="", card_size=(200, 220), mode='vertical', parent=None):
        super().__init__(parent)
        self.game = game
        self.title = title
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

    def _setup_vertical_layout(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        image_label = QLabel()
        image_label.setObjectName("GameCardImage")
        if self.game and self.game.get("image") and os.path.exists(self.game["image"]):
            pixmap = QPixmap(self.game["image"]).scaled(self.card_size[0] - 20, self.card_size[1] - 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            placeholder_pixmap = QPixmap(self.card_size[0] - 20, self.card_size[1] - 50)
            placeholder_pixmap.fill(QColor("#333"))
            painter = QPainter(placeholder_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(placeholder_pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Sem Imagem")
            painter.end()
            image_label.setPixmap(placeholder_pixmap)

        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        name_label = QLabel(self.game["name"])
        name_label.setObjectName("GameCardName")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

    def _setup_horizontal_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        image_label = QLabel()
        image_label.setFixedSize(220, 160)
        main_layout.addWidget(image_label)

        image_to_display = self.game.get("header_path") or self.game.get("image")
        if self.game and image_to_display and os.path.exists(image_to_display):
            pixmap = QPixmap(image_to_display).scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(5, 5, 5, 5)

        title_label = QLabel(self.title)
        title_label.setObjectName("HorizontalCardTitle")
        name_label = QLabel(self.game["name"])
        name_label.setObjectName("HorizontalCardGameName")
        name_label.setWordWrap(True)
        playtime_seconds = self.game.get("total_playtime", 0)
        playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas")
        playtime_label.setObjectName("HorizontalCardGamePlaytime")

        info_layout.addWidget(title_label)
        info_layout.addWidget(name_label)
        info_layout.addStretch()
        info_layout.addWidget(playtime_label)
        main_layout.addLayout(info_layout, 1)

    # --- MÉTODOS RESTAURADOS ---
    def _setup_shadow(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(5)
        self.shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(self.shadow)

    def _setup_animation(self):
        self.enter_animation = QPropertyAnimation(self, b"geometry")
        self.enter_animation.setDuration(150)
        self.enter_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.leave_animation = QPropertyAnimation(self, b"geometry")
        self.leave_animation.setDuration(150)
        self.leave_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        current_geo = self.geometry()
        start_geo = QRect(current_geo.x(), current_geo.y(), self.width(), self.height())
        end_geo = QRect(current_geo.x() - 5, current_geo.y() - 5, self.width() + 10, self.height() + 10)
        self.enter_animation.setStartValue(start_geo)
        self.enter_animation.setEndValue(end_geo)
        self.leave_animation.stop()
        self.enter_animation.start()
        self.raise_()
        super().enterEvent(event)

    def leaveEvent(self, event):
        start_geo = self.geometry()
        end_geo = QRect(start_geo.x() + 5, start_geo.y() + 5, self.width() - 10, self.height() - 10)
        self.leave_animation.setStartValue(start_geo)
        self.leave_animation.setEndValue(end_geo)
        self.enter_animation.stop()
        self.leave_animation.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.shadow.setBlurRadius(15)
            self.shadow.setYOffset(2)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.shadow.setBlurRadius(25)
            self.shadow.setYOffset(5)
        super().mouseReleaseEvent(event)