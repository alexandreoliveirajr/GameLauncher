# gui/animated_card.py (VERSÃO FINAL COM ARQUITETURA DEFINITIVA)

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPixmap, QColor, QPainter, QIcon, QPainterPath
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, Qt, pyqtSignal, QSize, QRectF

class AnimatedGameCard(QFrame):
    clicked = pyqtSignal()

    # --- NOSSAS REGRAS DE DESIGN ---
    CARD_WIDTH = 210
    IMAGE_ASPECT_RATIO = 1.5 # (Proporção 3:2, como 450/300)
    TEXT_AREA_HEIGHT = 55

    IMAGE_HEIGHT = int(CARD_WIDTH * IMAGE_ASPECT_RATIO)
    CARD_HEIGHT = IMAGE_HEIGHT + TEXT_AREA_HEIGHT
    CARD_SIZE = QSize(CARD_WIDTH, CARD_HEIGHT)
    # --------------------------------

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

        # 1. ÁREA DA IMAGEM (com altura calculada)
        self.image_label = QLabel()
        self.image_label.setObjectName("GameCardImage")
        self.image_label.setFixedHeight(self.IMAGE_HEIGHT)

        # 2. ÁREA DO TEXTO (com layout horizontal)
        text_container = QFrame()
        text_container.setObjectName("GameCardTextContainer")
        text_container.setFixedHeight(self.TEXT_AREA_HEIGHT)

        text_layout = QHBoxLayout(text_container)
        text_layout.setContentsMargins(12, 0, 12, 0) # Padding horizontal

        self.name_label = QLabel(self.game["name"])
        self.name_label.setObjectName("GameCardName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.platform_icon_label = QLabel()
        self.platform_icon_label.setObjectName("PlatformIcon")
        self.platform_icon_label.setFixedSize(24, 24) # Tamanho do ícone
        self._update_platform_icon()

        text_layout.addWidget(self.name_label, 1) # O '1' faz o nome ocupar o espaço
        text_layout.addWidget(self.platform_icon_label)

        main_layout.addWidget(self.image_label)
        main_layout.addWidget(text_container)

    def _update_platform_icon(self):
        source = self.game.get("source", "local").lower()
        icon_path = f"assets/icons/{source}.svg"
        if not os.path.exists(icon_path):
            icon_path = "assets/icons/local.svg" # Fallback para um ícone local

        if os.path.exists(icon_path):
            self.platform_icon_label.setPixmap(QPixmap(icon_path))
            self.platform_icon_label.setScaledContents(True)

    def _load_and_scale_pixmap(self):
        image_path = self.game.get("image")
        target_size = self.image_label.size()

        if target_size.width() == 0 or target_size.height() == 0: return

        if not (image_path and os.path.exists(image_path)):
            placeholder = QPixmap(target_size); placeholder.fill(QColor("#333"))
            painter = QPainter(placeholder); painter.setPen(QColor("#FFFFFF"))
            font = self.font(); font.setPointSize(12); painter.setFont(font)
            painter.drawText(placeholder.rect(), int(Qt.AlignmentFlag.AlignCenter), "Sem Imagem")
            painter.end(); self.image_label.setPixmap(placeholder); return

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
        self.enter_animation = QPropertyAnimation(self, b"geometry")
        self.enter_animation.setDuration(150); self.enter_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.leave_animation = QPropertyAnimation(self, b"geometry")
        self.leave_animation.setDuration(150); self.leave_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        current_geo = self.geometry()
        end_geo = QRect(current_geo.x() - 5, current_geo.y() - 5, self.width() + 10, self.height() + 10)
        self.enter_animation.setStartValue(self.geometry()); self.enter_animation.setEndValue(end_geo)
        self.leave_animation.stop(); self.enter_animation.start(); self.raise_(); super().enterEvent(event)

    def leaveEvent(self, event):
        start_geo = self.geometry()
        end_geo = QRect(start_geo.x() + 5, start_geo.y() + 5, self.width() - 10, self.height() - 10)
        self.leave_animation.setStartValue(start_geo); self.leave_animation.setEndValue(end_geo)
        self.enter_animation.stop(); self.leave_animation.start(); super().leaveEvent(event)