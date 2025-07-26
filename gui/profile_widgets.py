# gui/profile_widgets.py

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt, QSize

class StatBox(QWidget):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.value_label = QLabel(str(value))
        
        self.title_label = QLabel(title.upper())
        
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        
        self.setAutoFillBackground(True)
        