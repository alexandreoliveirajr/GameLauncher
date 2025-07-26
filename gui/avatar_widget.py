# gui/avatar_widget.py

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QBitmap, QColor
from PyQt6.QtCore import Qt, QSize, QPoint


class AvatarWidget(QWidget):
    def __init__(self, size=150, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(size, size)
        
        self.movie = None

    def set_image(self, image_path):
        if self.movie:
            self.movie.stop()
            self.movie = None

        if image_path and image_path.lower().endswith('.gif'):
            from PyQt6.QtGui import QMovie
            self.movie = QMovie(image_path)
            self.movie.setScaledSize(QSize(self.width(), self.height()))
            self.image_label.setMovie(self.movie)
            self.movie.start()
        elif image_path:
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("SEM\nAVATAR")
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def paintEvent(self, event):
        # Cria uma máscara redonda para aplicar ao widget
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Máscara com cantos arredondados
        mask = QBitmap(self.size())
        mask.fill(Qt.GlobalColor.white) # MUDANÇA AQUI
        mask_painter = QPainter(mask)
        mask_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        mask_painter.setBrush(Qt.GlobalColor.black) # MUDANÇA AQUI
        mask_painter.drawRoundedRect(self.rect(), 20, 20)
        mask_painter.end()

        self.image_label.setMask(mask)
        super().paintEvent(event)