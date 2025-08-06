# gui/animated_card.py

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QGraphicsColorizeEffect
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, Qt, pyqtSignal, QSize, QRectF, QPoint

class AnimatedGameCard(QFrame):
    clicked = pyqtSignal()
    
    CARD_WIDTH = 210
    IMAGE_ASPECT_RATIO = 1.5
    TEXT_AREA_HEIGHT = 55
    IMAGE_HEIGHT = int(CARD_WIDTH * IMAGE_ASPECT_RATIO)
    CARD_HEIGHT = IMAGE_HEIGHT + TEXT_AREA_HEIGHT
    CARD_SIZE = QSize(CARD_WIDTH, CARD_HEIGHT)

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.setObjectName("GameCard")
        self.game = game
        self.setFixedSize(self.CARD_SIZE)
        
        self._setup_ui()
        self._setup_animation()
        self._setup_shadow()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setObjectName("GameCardImage")
        self.image_label.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_container = QFrame()
        text_container.setObjectName("GameCardTextContainer")
        text_container.setFixedHeight(self.TEXT_AREA_HEIGHT)

        v_text_layout = QVBoxLayout(text_container)
        v_text_layout.setContentsMargins(12, 0, 12, 0)
        v_text_layout.setSpacing(0)

        content_widget = QWidget()
        h_content_layout = QHBoxLayout(content_widget)
        h_content_layout.setContentsMargins(0, 0, 0, 0)
        h_content_layout.setSpacing(10)

        self.name_label = QLabel(self.game["name"])
        self.name_label.setObjectName("GameCardName")
        self.name_label.setWordWrap(True)

        self.platform_icon_label = QLabel()
        self.platform_icon_label.setObjectName("PlatformIcon")
        self.platform_icon_label.setFixedSize(24, 24)
        self._update_platform_icon()

        h_content_layout.addWidget(self.name_label, 1)
        h_content_layout.addWidget(self.platform_icon_label)

        v_text_layout.addStretch(1)
        v_text_layout.addWidget(content_widget)
        v_text_layout.addStretch(1)

        main_layout.addWidget(self.image_label)
        main_layout.addWidget(text_container)

    def _update_platform_icon(self):
        source = self.game.get("source", "local").lower()
        icon_path = f"assets/icons/platform/{source}.svg"
        if not os.path.exists(icon_path):
            icon_path = "assets/icons/platform/local.svg"
        if os.path.exists(icon_path):
            self.platform_icon_label.setPixmap(QPixmap(icon_path))
            self.platform_icon_label.setScaledContents(True)

    def _load_and_scale_pixmap(self):
        image_path = self.game.get("image_path")
        target_size = self.image_label.size()

        if target_size.width() == 0 or target_size.height() == 0: return

        if not (image_path and os.path.exists(image_path)):
            placeholder = QPixmap(target_size); placeholder.fill(QColor("#333"))
            painter = QPainter(placeholder); painter.setPen(QColor("#FFFFFF"))
            font = self.font(); font.setPointSize(12); painter.setFont(font)
            painter.drawText(placeholder.rect(), int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), self.game["name"])
            painter.end(); self.image_label.setPixmap(placeholder)
        else:
            source_pixmap = QPixmap(image_path)
            is_vertical = source_pixmap.height() > source_pixmap.width()
            
            if is_vertical:
                scaled_pixmap = source_pixmap.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            else:
                canvas = QPixmap(target_size); canvas.fill(QColor("#333"))
                scaled_art = source_pixmap.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                painter = QPainter(canvas)
                x = (target_size.width() - scaled_art.width()) / 2
                y = (target_size.height() - scaled_art.height()) / 2
                painter.drawPixmap(int(x), int(y), scaled_art); painter.end()
                scaled_pixmap = canvas

            self.image_label.setPixmap(scaled_pixmap)
        
        # --- INÍCIO DA ADIÇÃO ---
        # Após carregar a imagem, aplica o efeito visual com base no status do jogo
        self._apply_status_effect()
        # --- FIM DA ADIÇÃO ---

    def _apply_status_effect(self):
        """Aplica um efeito de escala de cinza se o jogo não estiver instalado."""
        is_installed = self.game.get("status", "UNINSTALLED") == "INSTALLED"
        
        if not is_installed:
            effect = QGraphicsColorizeEffect()
            # Define a cor para um cinza médio com alguma transparência para dessaturar a imagem
            effect.setColor(QColor(128, 128, 128))
            effect.setStrength(0.8) # Força do efeito, 1.0 é totalmente cinza
            self.image_label.setGraphicsEffect(effect)
        else:
            # Garante que jogos instalados não tenham nenhum efeito
            self.image_label.setGraphicsEffect(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._load_and_scale_pixmap()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _setup_shadow(self):
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25); self.shadow.setXOffset(0); self.shadow.setYOffset(5)
        self.shadow.setColor(QColor(0, 0, 0, 160)); self.setGraphicsEffect(self.shadow)

    def _setup_animation(self):
        self.rest_geometry = QRect(5, 5, self.CARD_WIDTH, self.CARD_HEIGHT)
        self.hover_geometry = QRect(0, 0, self.CARD_WIDTH + 10, self.CARD_HEIGHT + 10)
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(120)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        self.raise_()
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(self.hover_geometry)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(self.rest_geometry)
        self.animation.start()
        super().leaveEvent(event)
