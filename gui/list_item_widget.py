# gui/list_item_widget.py

import os
# Importações completas, incluindo as de animação e efeitos
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from core.theme import current_theme

class GameListItemWidget(QWidget):
    details_clicked = pyqtSignal()
    play_clicked = pyqtSignal()

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.setMinimumHeight(100)
        self.setMaximumHeight(100)
        
        self.is_hovered = False
        self.setMouseTracking(True)
        
        self._setup_ui()
        # Chamada para a nova função que configura os efeitos
        self._setup_effects()

    def _setup_ui(self):
        # A UI interna não muda
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

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
            image_label.setText("Sem Arte")
            image_label.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; color: #888;")
        main_layout.addWidget(image_label)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 5, 0, 5)
        name_label = QLabel(self.game["name"])
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; background: transparent;")
        
        playtime_seconds = self.game.get("total_playtime", 0)
        playtime_hours = playtime_seconds / 3600
        playtime_label = QLabel(f"{playtime_hours:.1f} horas jogadas")
        playtime_label.setStyleSheet("font-size: 13px; color: #ccc; background: transparent;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(playtime_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

        self.play_btn = QPushButton("▶ Jogar")
        self.play_btn.setFixedSize(100, 40)
        self.play_btn.setStyleSheet("""
            QPushButton { background-color: #2c9a48; color: white; font-size: 14px; font-weight: bold; border-radius: 5px; } 
            QPushButton:hover { background-color: #36b558; }
        """)
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
        self.enter_animation.setEasingCurve(QEasingCurve.OutQuad)

        # Animação de Saída (Desinflar)
        self.leave_animation = QPropertyAnimation(self, b"geometry")
        self.leave_animation.setDuration(150)
        self.leave_animation.setEasingCurve(QEasingCurve.OutQuad)

    # O paintEvent continua o mesmo, cuidando do fundo e da borda
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        backgroundColor = current_theme["card"]
        borderColor = current_theme["accent"] if self.is_hovered else current_theme["card_border"]
        painter.setPen(QPen(borderColor, 1))
        painter.setBrush(QBrush(backgroundColor))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)

    # --- EVENTOS DE MOUSE ATUALIZADOS COM ANIMAÇÃO ---
    def enterEvent(self, event):
        self.is_hovered = True
        self.update() # Força redesenho da borda
        
        # Armazena a geometria original e define a animação de inflar
        self.original_geometry = self.geometry()
        end_geo = self.original_geometry.adjusted(-2, -2, 4, 4) # Infla em 2px para cada lado
        
        self.leave_animation.stop()
        self.enter_animation.setStartValue(self.geometry())
        self.enter_animation.setEndValue(end_geo)
        self.enter_animation.start()
        
        self.raise_() # Coloca o widget na frente dos outros
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update() # Força redesenho da borda
        
        # Inicia a animação para retornar ao tamanho original
        self.enter_animation.stop()
        self.leave_animation.setStartValue(self.geometry())
        self.leave_animation.setEndValue(self.original_geometry)
        self.leave_animation.start()
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        try:
            if self.play_btn and not self.play_btn.geometry().contains(event.pos()):
                if event.button() == Qt.LeftButton:
                    self.details_clicked.emit()
            
            super().mousePressEvent(event)

        except RuntimeError as e:
            pass