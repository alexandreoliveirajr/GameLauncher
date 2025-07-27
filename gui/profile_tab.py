# gui/profile_tab.py

import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, 
    QScrollArea, QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtGui import QPainter, QColor, QBrush, QPixmap, QColor
from PyQt6.QtCore import Qt, QPoint

from gui.edit_profile_dialog import EditProfileDialog
from gui.profile_widgets import StatBox
from gui.avatar_widget import AvatarWidget
from gui.animated_card import AnimatedGameCard

class ShowcaseCardWidget(QFrame):
    def __init__(self, game, title, parent=None):
        super().__init__(parent)
        self.setObjectName("ShowcaseCard")
        self.game = game
        self.setFixedHeight(160)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Imagem à esquerda
        image_label = QLabel()
        image_label.setObjectName("ShowcaseCardImage")
        image_label.setFixedSize(220, 130) # Tamanho da arte horizontal
        image_path = self.game.get("header_path") or self.game.get("image")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(image_label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
        main_layout.addWidget(image_label)

        # Textos à direita
        info_layout = QVBoxLayout()
        title_label = QLabel(title.upper())
        title_label.setObjectName("ShowcaseCardTitle")

        name_label = QLabel(self.game["name"])
        name_label.setObjectName("ShowcaseCardGameName")

        info_layout.addWidget(title_label)
        info_layout.addWidget(name_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout, 1)

class ProfileTab(QWidget):
    # (O __init__, paintEvent, e _setup_ui continuam os mesmos)
    def __init__(self, profile_manager, game_manager, main_window_ref):
        super().__init__()
        self.profile_manager = profile_manager
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        self.background_pixmap = None
        self._setup_ui()
        self.load_profile_data()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.background_pixmap:
            target_rect = self.rect()
            scaled_pixmap = self.background_pixmap.scaled(target_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint((target_rect.width() - scaled_pixmap.width()) // 2, (target_rect.height() - scaled_pixmap.height()) // 2)
            painter.drawPixmap(point, scaled_pixmap)
        else:
            painter.fillRect(self.rect(), QBrush(QColor("#1e1e1e")))
    
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 20)
        self.main_layout.setSpacing(20)
        header_panel = QWidget()
        header_layout = QHBoxLayout(header_panel)
        header_layout.setContentsMargins(20, 20, 20, 20)
        self.avatar_widget = AvatarWidget(size=180)
        header_layout.addWidget(self.avatar_widget)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(20, 0, 0, 0)
        self.username_label = QLabel()
        self.bio_label = QLabel()
        self.bio_label.setWordWrap(True)
        info_layout.addWidget(self.username_label)
        info_layout.addWidget(self.bio_label)
        info_layout.addStretch()
        header_layout.addLayout(info_layout, 1)
        edit_button = QPushButton("✏️ Editar Perfil")
        edit_button.clicked.connect(self.edit_profile)
        header_layout.addWidget(edit_button, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(header_panel)
        self.main_layout.addStretch(1)
        showcase_title = QLabel("JOGOS EM DESTAQUE")
        showcase_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(showcase_title)
        self.showcase_layout = QHBoxLayout()
        self.showcase_layout.setSpacing(20)
        self.main_layout.addLayout(self.showcase_layout)
        self.main_layout.addStretch(1)
        self.stats_layout = QHBoxLayout()
        self.main_layout.addLayout(self.stats_layout)

    def load_profile_data(self):
        profile_data = self.profile_manager.get_data()
        bg_path = profile_data.get("background_path")
        if bg_path and os.path.exists(bg_path):
            self.background_pixmap = QPixmap(bg_path)
        else:
            self.background_pixmap = None
        self.update()
        self.username_label.setText(profile_data.get("username", "Player1"))
        self.bio_label.setText(profile_data.get("bio", "Sem bio."))
        avatar_path = profile_data.get("avatar_path")
        self.avatar_widget.set_image(avatar_path)
        self._populate_stats_and_showcase()
    
    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                elif item.layout() is not None:
                    self._clear_layout(item.layout())

    def _populate_stats_and_showcase(self):
        self._clear_layout(self.showcase_layout)
        self._clear_layout(self.stats_layout)

        all_games = self.game_manager.get_all_games()
        profile_data = self.profile_manager.get_data()

        most_played_game = None
        if all_games:
            most_played_game = max(all_games, key=lambda g: g.get("total_playtime", 0))
            if most_played_game.get("total_playtime", 0) == 0:
                most_played_game = None
        favorite_game = None
        showcased_favorite_id = profile_data.get("showcased_favorite_id")
        if showcased_favorite_id:
            favorite_game = self.game_manager.get_game_by_id(showcased_favorite_id)
        if not favorite_game:
            favorite_games_list = self.game_manager.get_favorite_games()
            if favorite_games_list:
                favorite_game = favorite_games_list[0]
        # --- FIM DA LÓGICA CORRIGIDA ---
        
        recent_games = self.game_manager.get_recent_games()
        last_played_game = recent_games[0] if recent_games else None

        self.showcase_layout.addStretch(1)
        if favorite_game:
            card = ShowcaseCardWidget(favorite_game, title="JOGO FAVORITO")
            self.showcase_layout.addWidget(card)
        if most_played_game:
            card = ShowcaseCardWidget(most_played_game, title="MAIS JOGADO")
            self.showcase_layout.addWidget(card)
        if last_played_game:
            card = ShowcaseCardWidget(last_played_game, title="ÚLTIMO JOGO JOGADO")
            self.showcase_layout.addWidget(card)
        self.showcase_layout.addStretch(1)

        favorite_games_list_for_count = self.game_manager.get_favorite_games()
        total_playtime_seconds = sum(g.get("total_playtime", 0) for g in all_games)
        total_playtime_hours = total_playtime_seconds // 3600
        creation_date_str = profile_data.get("creation_date", "")
        member_since_str = "N/A"
        if creation_date_str:
            try:
                dt = datetime.fromisoformat(creation_date_str)
                member_since_str = dt.strftime("%b %Y")
            except:
                pass

        self.stats_layout.addStretch(1)
        self.stats_layout.addWidget(StatBox("HORAS TOTAIS", f"~{total_playtime_hours}"))
        self.stats_layout.addWidget(StatBox("JOGOS NA BIBLIOTECA", len(all_games)))
        self.stats_layout.addWidget(StatBox("MEMBRO DESDE", member_since_str))
        self.stats_layout.addStretch(1)

    def edit_profile(self):
        dialog = EditProfileDialog(self.profile_manager, self.game_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print("Perfil salvo! Atualizando a exibição...")
            self.load_profile_data()