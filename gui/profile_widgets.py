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

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("StatValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("StatTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        