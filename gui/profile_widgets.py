# gui/profile_widgets.py

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QSize
from core.theme import current_theme

class StatBox(QWidget):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"font-size: 26px; font-weight: bold; border: none; background: transparent; color: {current_theme['text_primary'].name()};")
        
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(f"font-size: 11px; color: {current_theme['text_secondary'].name()}; border: none; background: transparent;")

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        
        # --- 2. CORREÇÃO DA STYLESHEET ---
        panel_color = current_theme['panel_background']
        r, g, b, a = panel_color.getRgb()

        self.setAutoFillBackground(True)
        self.setStyleSheet(f"""
            QWidget {{ 
                background-color: rgba({r}, {g}, {b}, {a}); 
                border-radius: 12px; 
            }}
        """)
