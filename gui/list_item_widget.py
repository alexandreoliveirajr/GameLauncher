# gui/list_item_widget.py

import os
# Importações completas, incluindo as de animação e efeitos
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect

class GameListItemWidget(QWidget):
    details_clicked = pyqtSignal()
    play_clicked = pyqtSignal()

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.setObjectName("GameListItem")
        self.game = game
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)
        
        self.is_hovered = False
        self.setMouseTracking(True)
        
        self._setup_ui()
        # Chamada para a nova função que configura os efeitos
        self._setup_effects()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        image_label = QLabel()
        image_label.setFixedSize(140, 80)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image_to_display = self.game.get("header_path") or self.game.get("image")
        
        if image_to_display and os.path.exists(image_to_display):
            pixmap = QPixmap(image_to_display)
            scaled_pixmap = pixmap.scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("Sem Arte")
            
        main_layout.addWidget(image_label)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 5, 0, 5)
        name_label = QLabel(self.game["name"])
        
        playtime_seconds = self.game.get("total_playtime", 0)
        playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(playtime_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        self.play_btn = QPushButton("▶ Jogar")
        self.play_btn.setFixedSize(100, 40)
        self.play_btn.clicked.connect(self.play_clicked.emit)
        main_layout.addWidget(self.play_btn)
    
    # --- NOVO MÉTODO PARA CONFIGURAR EFEITOS ---
    def _setup_effects(self):
        # Efeito de Sombra
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(self.shadow)

        # Animação de Entrada (Inflar)
        self.enter_animation = QPropertyAnimation(self, b"geometry")
        self.enter_animation.setDuration(150)
        self.enter_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Animação de Saída (Desinflar)
        self.leave_animation = QPropertyAnimation(self, b"geometry")
        self.leave_animation.setDuration(150)
        self.leave_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    # --- EVENTOS DE MOUSE ATUALIZADOS COM ANIMAÇÃO ---
    def enterEvent(self, event):
        self.original_geometry = self.geometry()
        end_geo = self.original_geometry.adjusted(-2, -2, 4, 4) # Infla em 2px para cada lado
        
        self.leave_animation.stop()
        self.enter_animation.setStartValue(self.geometry())
        self.enter_animation.setEndValue(end_geo)
        self.enter_animation.start()
        
        self.raise_() # Coloca o widget na frente dos outros
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Inicia a animação para retornar ao tamanho original
        self.enter_animation.stop()
        self.leave_animation.setStartValue(self.geometry())
        self.leave_animation.setEndValue(self.original_geometry)
        self.leave_animation.start()
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        try:
            if self.play_btn and not self.play_btn.geometry().contains(event.pos()):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.details_clicked.emit()
            
            super().mousePressEvent(event)

        except RuntimeError as e:
            pass