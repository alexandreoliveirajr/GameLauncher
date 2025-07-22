# gui/profile_widgets.py

import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QSize

class StatBox(QWidget):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("font-size: 26px; font-weight: bold; border: none; background: transparent; color: white;")
        self.value_label.setAlignment(Qt.AlignCenter)
        
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("font-size: 11px; color: #aaa; border: none; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        
        self.setAutoFillBackground(True)
        self.setStyleSheet("QWidget { background-color: rgba(42, 45, 48, 0.75); border-radius: 12px; }")
