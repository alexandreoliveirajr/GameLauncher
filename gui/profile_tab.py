# gui/profile_tab.py (VERSÃO DE POLIMENTO FINAL)

import os
import pycountry
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, 
    QFrame, QStackedLayout, QGraphicsBlurEffect
)
from PyQt6.QtGui import QPainter, QBrush, QPixmap, QColor, QIcon
from PyQt6.QtCore import Qt, QPoint, QSize

from gui.edit_profile_dialog import EditProfileDialog
from gui.profile_widgets import StatBox
from gui.avatar_widget import AvatarWidget


class ShowcaseCardWidget(QFrame):
    def __init__(self, game, title, parent=None):
        super().__init__(parent)
        self.setObjectName("ShowcaseCard")
        self.game = game
        self.setFixedSize(300, 220)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        image_label = QLabel()
        image_label.setObjectName("ShowcaseCardImage")
        
        # O fundo do QLabel da imagem será preto para o efeito "letterbox"
        image_label.setStyleSheet("background-color: black;")

        image_path = self.game.get("header_path") or self.game.get("background") or self.game.get("image")
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            
            # MUDANÇA: De KeepAspectRatioByExpanding para KeepAspectRatio
            # Isso garante que a imagem inteira seja visível (efeito letterbox)
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, # <--- MUDANÇA AQUI
                Qt.TransformationMode.SmoothTransformation
            )
            image_label.setPixmap(scaled_pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Centraliza a imagem no label

        main_layout.addWidget(image_label)

        overlay = QFrame(self)
        overlay.setObjectName("ShowcaseCardOverlay")
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.4);")
        
        info_container = QWidget(self)
        info_container.setStyleSheet("background-color: transparent;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel(title.upper()); title_label.setObjectName("ShowcaseCardTitle")
        game_name_label = QLabel(self.game["name"]); game_name_label.setObjectName("ShowcaseCardGameName"); game_name_label.setWordWrap(True)

        info_layout.addWidget(title_label)
        info_layout.addWidget(game_name_label)
        info_layout.addStretch()

        stats_layout = QHBoxLayout()
        playtime_seconds = self.game.get("total_playtime", 0) or 0
        playtime_hours = playtime_seconds / 3600
        stats_layout.addWidget(self._create_micro_stat("assets/icons/clock.svg", f"{playtime_hours:.1f}h"))
        
        last_play_str = "Nunca"
        last_play_iso = self.game.get('last_play_time')
        if last_play_iso:
            try: last_play_str = datetime.fromisoformat(last_play_iso).strftime("%d/%m/%y")
            except (ValueError, TypeError): last_play_str = "Data Inválida"
        stats_layout.addWidget(self._create_micro_stat("assets/icons/calendar.svg", last_play_str))

        source = self.game.get('source', 'local')
        platform_icon_path = f"assets/icons/platform/{source.lower()}.svg"
        stats_layout.addWidget(self._create_micro_stat(platform_icon_path, ""))
        stats_layout.addStretch()

        info_layout.addLayout(stats_layout)
        main_layout.addWidget(info_container)

    def resizeEvent(self, event):
        self.findChild(QFrame, "ShowcaseCardOverlay").resize(event.size())
        self.findChild(QWidget).resize(event.size())
        super().resizeEvent(event)

    def _create_micro_stat(self, icon_path, text):
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)
        icon = QLabel()
        if os.path.exists(icon_path):
            icon.setPixmap(QPixmap(icon_path))
        icon.setFixedSize(16, 16); icon.setScaledContents(True)
        label = QLabel(text); label.setObjectName("ShowcaseCardStatLabel")
        layout.addWidget(icon)
        layout.addWidget(label)
        return widget


class ProfileTab(QWidget):
    def __init__(self, profile_manager, game_manager, main_window_ref):
        super().__init__()
        self.profile_manager = profile_manager
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        self.setAutoFillBackground(False)
        self._setup_ui()
        self.load_profile_data()

    def _setup_ui(self):
        # MUDANÇA: Usamos layout manual para controle total
        self.background_label = QLabel(self)
        self.background_label.setObjectName("ProfileBackground")
        self.background_label.setScaledContents(True)
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(5)
        self.background_label.setGraphicsEffect(self.blur_effect)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ProfileScrollArea")
        self.scroll_area.setAutoFillBackground(False)
        self.scroll_area.viewport().setAutoFillBackground(False)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(25)
        self.scroll_area.setWidget(content_widget)

        # --- SEÇÃO DO CABEÇALHO ---
        header_panel = QFrame(); header_panel.setObjectName("ProfileHeaderPanel")
        header_layout = QHBoxLayout(header_panel)
        self.avatar_frame = QFrame(); self.avatar_frame.setObjectName("AvatarFrame")
        avatar_frame_layout = QVBoxLayout(self.avatar_frame); self.avatar_widget = AvatarWidget(size=150); avatar_frame_layout.addWidget(self.avatar_widget); header_layout.addWidget(self.avatar_frame)
        info_layout = QVBoxLayout(); info_layout.setContentsMargins(20, 0, 0, 0)
        name_layout = QHBoxLayout()
        self.username_label = QLabel(); self.username_label.setObjectName("ProfileUsername")
        self.flag_label = QLabel(); self.flag_label.setObjectName("ProfileFlag"); self.flag_label.setFixedHeight(24)
        name_layout.addWidget(self.username_label); name_layout.addWidget(self.flag_label); name_layout.addStretch()
        self.real_name_label = QLabel(); self.real_name_label.setObjectName("ProfileRealName"); self.bio_label = QLabel(); self.bio_label.setWordWrap(True)
        info_layout.addLayout(name_layout); info_layout.addWidget(self.real_name_label); info_layout.addWidget(self.bio_label); info_layout.addStretch()
        header_layout.addLayout(info_layout, 1)
        edit_button = QPushButton(" Editar Perfil"); edit_button.setObjectName("ProfileEditButton"); edit_button.setIcon(QIcon("assets/icons/sliders.svg")); edit_button.clicked.connect(self.edit_profile)
        header_layout.addWidget(edit_button, alignment=Qt.AlignmentFlag.AlignTop)
        
        # --- SEÇÃO DE JOGOS EM DESTAQUE ---
        showcase_panel = QFrame(); showcase_panel.setObjectName("ProfileShowcasePanel")
        showcase_panel_layout = QVBoxLayout(showcase_panel)
        showcase_title = QLabel("JOGOS EM DESTAQUE"); showcase_title.setObjectName("SectionTitle")
        showcase_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # <--- MUDANÇA AQUI
        self.showcase_layout = QHBoxLayout()
        showcase_panel_layout.addWidget(showcase_title)
        showcase_panel_layout.addLayout(self.showcase_layout)

        # --- SEÇÃO DE ESTATÍSTICAS ---
        stats_panel = QFrame(); stats_panel.setObjectName("ProfileStatsPanel")
        stats_panel_layout = QVBoxLayout(stats_panel)
        stats_title = QLabel("ESTATÍSTICAS"); stats_title.setObjectName("SectionTitle")
        stats_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # <--- MUDANÇA AQUI
        self.stats_layout = QHBoxLayout()
        stats_panel_layout.addWidget(stats_title)
        stats_panel_layout.addLayout(self.stats_layout)

        self.content_layout.addWidget(header_panel)
        self.content_layout.addWidget(showcase_panel)
        self.content_layout.addWidget(stats_panel)
        self.content_layout.addStretch(1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(self.rect())
        self.scroll_area.setGeometry(self.rect())

    def load_profile_data(self):
        profile_data = self.profile_manager.get_data()
        bg_path = profile_data.get("background_path")
        if bg_path and os.path.exists(bg_path): self.background_label.setPixmap(QPixmap(bg_path))
        else: self.background_label.clear()

        self.username_label.setText(profile_data.get("username", "Player1"))
        self.bio_label.setText(profile_data.get("bio", "Adicione sua bio aqui..."))
        real_name = profile_data.get("real_name")
        self.real_name_label.setText(real_name or "")
        self.real_name_label.setVisible(bool(real_name))

        country_code = profile_data.get("country_code")
        self.flag_label.setVisible(False)
        if country_code:
            flag_path = f"assets/flags/{country_code.upper()}.svg"
            if os.path.exists(flag_path):
                pixmap = QPixmap(flag_path)
                scaled_pixmap = pixmap.scaledToHeight(self.flag_label.height(), Qt.TransformationMode.SmoothTransformation)
                self.flag_label.setPixmap(scaled_pixmap)
                self.flag_label.setVisible(True)

        self.avatar_widget.set_image(profile_data.get("avatar_path"))
        self._populate_stats_and_showcase()
    
    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater()
    def _populate_stats_and_showcase(self):
        self._clear_layout(self.showcase_layout); self._clear_layout(self.stats_layout)
        all_games = self.game_manager.get_all_games(); profile_data = self.profile_manager.get_data()
        most_played = max(all_games, key=lambda g: g.get("total_playtime", 0)) if all_games else None
        showcased_favorite_id = profile_data.get("showcased_favorite_id"); showcased_favorite = self.game_manager.get_game_by_id(showcased_favorite_id) if showcased_favorite_id else None
        recent_games = self.game_manager.get_recent_games(); last_played = recent_games[0] if recent_games else None
        self.showcase_layout.addStretch(1)
        if showcased_favorite: self.showcase_layout.addWidget(ShowcaseCardWidget(showcased_favorite, "Jogo Favorito"))
        if most_played and most_played.get("total_playtime", 0) > 0: self.showcase_layout.addWidget(ShowcaseCardWidget(most_played, "Mais Jogado"))
        if last_played: self.showcase_layout.addWidget(ShowcaseCardWidget(last_played, "Último Jogo"))
        self.showcase_layout.addStretch(1)
        total_playtime = sum(g.get("total_playtime", 0) for g in all_games); total_hours = total_playtime / 3600
        self.stats_layout.addStretch(1)
        self.stats_layout.addWidget(StatBox("HORAS TOTAIS", f"~{int(total_hours)}")); self.stats_layout.addWidget(StatBox("JOGOS NA BIBLIOTECA", str(len(all_games)))); self.stats_layout.addWidget(StatBox("GÊNERO FAVORITO", self.game_manager.get_most_common_genre())); self.stats_layout.addStretch(1)
    def edit_profile(self):
        dialog = EditProfileDialog(self.profile_manager, self.game_manager, self)
        if dialog.exec(): self.load_profile_data()