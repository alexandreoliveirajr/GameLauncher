# gui/animated_card.py (VERSÃO FINAL COM LAYOUT HÍBRIDO E ALINHAMENTO PERFEITO)

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
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

        # 1. ÁREA DA IMAGEM (continua igual)
        self.image_label = QLabel()
        self.image_label.setObjectName("GameCardImage")
        self.image_label.setFixedHeight(self.IMAGE_HEIGHT)

        # 2. CONTAINER DA ÁREA DE TEXTO (continua igual)
        text_container = QFrame()
        text_container.setObjectName("GameCardTextContainer")
        text_container.setFixedHeight(self.TEXT_AREA_HEIGHT)

        # --- NOVA LÓGICA DE LAYOUT INTERNO ---
        # Usamos um layout vertical para centralizar nosso conteúdo na altura
        v_text_layout = QVBoxLayout(text_container)
        v_text_layout.setContentsMargins(12, 0, 12, 0) # Padding horizontal
        v_text_layout.setSpacing(0)

        # Widget que vai segurar o nome e o ícone lado a lado
        content_widget = QWidget()
        h_content_layout = QHBoxLayout(content_widget)
        h_content_layout.setContentsMargins(0, 0, 0, 0)
        h_content_layout.setSpacing(10)

        self.name_label = QLabel(self.game["name"])
        self.name_label.setObjectName("GameCardName")
        self.name_label.setWordWrap(True) # A quebra de linha continua funcionando

        self.platform_icon_label = QLabel()
        self.platform_icon_label.setObjectName("PlatformIcon")
        self.platform_icon_label.setFixedSize(24, 24)
        self._update_platform_icon()

        h_content_layout.addWidget(self.name_label, 1)
        h_content_layout.addWidget(self.platform_icon_label)

        # A MÁGICA DA CENTRALIZAÇÃO:
        v_text_layout.addStretch(1) # 1. Adiciona um calço flexível em cima
        v_text_layout.addWidget(content_widget) # 2. Adiciona nosso conteúdo
        v_text_layout.addStretch(1) # 3. Adiciona um calço flexível embaixo
        # ---------------------------

        main_layout.addWidget(self.image_label)
        main_layout.addWidget(text_container)

    def _update_platform_icon(self):
        source = self.game.get("source", "local").lower()
        # --- DEBUG ---
        print(f"Jogo: '{self.game['name']}', Source do DB: '{source}'")

        icon_path = f"assets/icons/platform/{source}.svg"
        print(f"Procurando ícone em: '{icon_path}'")
        # -------------

        if not os.path.exists(icon_path):
            # --- DEBUG ---
            print(f"-> Ícone NÃO encontrado! Usando fallback 'local.svg'.")
            # -------------
            icon_path = "assets/icons/platform/local.svg"

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
            painter.drawText(placeholder.rect(), int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), self.game["name"])
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
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150); self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos() - QPoint(0, 5))
        self.animation.start()
        self.raise_(); super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.stop()
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos() + QPoint(0, 5))
        self.animation.start(); super().leaveEvent(event)