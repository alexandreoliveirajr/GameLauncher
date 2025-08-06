# gui/game_page_widget.py

import os
from datetime import datetime
import webbrowser
import subprocess
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QTextEdit, QScrollArea, QMessageBox, QDialog, QSizePolicy)
from PyQt6.QtGui import QPixmap, QColor, QPainter, QBrush, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QSize, QTimer

from gui.game_edit_dialog import GameEditDialog
from utils.path_utils import get_absolute_path

class GamePageWidget(QWidget):
    back_clicked = pyqtSignal()
    def __init__(self, game_data, game_manager, game_launcher, main_window_ref, parent=None):
        super().__init__(parent)
        self.setObjectName("GamePage")
        self.game_data = game_data
        self.game_manager = game_manager
        self.game_launcher = game_launcher
        self.main_window_ref = main_window_ref
        self.background_pixmap = None
        self._setup_ui()
        self.load_game_data(self.game_data)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.background_pixmap and not self.background_pixmap.isNull():
            target_rect = self.rect()
            scaled_pixmap = self.background_pixmap.scaled(target_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint((target_rect.width() - scaled_pixmap.width()) // 2, (target_rect.height() - scaled_pixmap.height()) // 2)
            painter.drawPixmap(point, scaled_pixmap)
            overlay_color = QColor(20, 21, 24, 217)
            painter.fillRect(target_rect, QBrush(overlay_color))
        else:
            painter.fillRect(self.rect(), QBrush(QColor("#141518")))
        super().paintEvent(event)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        top_bar = QFrame(); top_bar.setObjectName("TopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        back_button = QPushButton("← Voltar"); back_button.setObjectName("BackButton")
        back_button.clicked.connect(self.back_clicked.emit)
        top_bar_layout.addWidget(back_button); top_bar_layout.addStretch()
        content_area = QScrollArea(); content_area.setObjectName("ContentArea")
        content_area.setWidgetResizable(True)
        content_area.viewport().setAutoFillBackground(False)
        content_container = QWidget()
        content_container.setObjectName("GamePageContentContainer") 
        content_area.setWidget(content_container)
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(35, 20, 35, 20)
        content_layout.setSpacing(35)
        left_column = QVBoxLayout(); left_column.setSpacing(15)
        self.cover_label = QLabel()
        self.cover_label.setObjectName("GameCoverImage")
        self.cover_label.setMaximumWidth(320)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.play_button = QPushButton("▶ JOGAR"); self.play_button.setObjectName("LargePlayButton")
        self.play_button.clicked.connect(self.launch_game)
        action_buttons_layout = QHBoxLayout()
        self.fav_button = QPushButton("Favoritar"); self.fav_button.setObjectName("FavoriteActionButton"); self.fav_button.setCheckable(True)
        self.edit_button = QPushButton("Editar"); self.edit_button.setObjectName("ActionButton")
        self.delete_button = QPushButton("Excluir"); self.delete_button.setObjectName("DeleteButton")
        action_buttons_layout.addWidget(self.fav_button)
        action_buttons_layout.addWidget(self.edit_button)
        action_buttons_layout.addWidget(self.delete_button)
        self.fav_button.clicked.connect(self._toggle_favorite)
        self.edit_button.clicked.connect(self._edit_game)
        self.delete_button.clicked.connect(self._delete_game)
        left_column.addWidget(self.cover_label)
        left_column.addWidget(self.play_button)
        left_column.addLayout(action_buttons_layout)
        left_column.addStretch()
        right_column = QVBoxLayout()
        self.title_label = QLabel(); self.title_label.setObjectName("GameTitleLabel"); self.title_label.setWordWrap(True)
        self.genres_layout = QHBoxLayout(); self.genres_layout.setObjectName("GenresLayout"); self.genres_layout.setSpacing(10)
        self.stats_layout = QHBoxLayout(); self.stats_layout.setObjectName("StatsLayout")
        self.stats_layout.setContentsMargins(0, 15, 0, 20)
        about_label = QLabel("SOBRE O JOGO"); about_label.setObjectName("SectionTitleLabel")
        self.summary_text = QTextEdit(); self.summary_text.setObjectName("GameSummaryText"); self.summary_text.setReadOnly(True)
        right_column.addWidget(self.title_label)
        right_column.addLayout(self.genres_layout)
        right_column.addLayout(self.stats_layout)
        right_column.addWidget(about_label)
        right_column.addWidget(self.summary_text, 1)
        content_layout.addLayout(left_column); content_layout.addLayout(right_column, 1)
        main_layout.addWidget(top_bar)
        main_layout.addWidget(content_area, 1)

    def launch_game(self):
        # --- INÍCIO DA ALTERAÇÃO ---
        # Verifica o status do jogo para decidir a ação
        is_installed = self.game_data.get("status", "UNINSTALLED") == "INSTALLED"
        source = self.game_data.get("source")
        app_id = self.game_data.get("app_id")

        # Se não estiver instalado e for da Steam, a ação é instalar
        if not is_installed and source == 'steam' and app_id:
            install_path = f"steam://install/{app_id}"
            logging.info(f"Iniciando instalação do jogo da Steam via protocolo: {install_path}")
            webbrowser.open(install_path)
            # Desabilita o botão para evitar múltiplos cliques
            self.play_button.setEnabled(False)
            self.play_button.setText("ABRINDO STEAM...")
            QTimer.singleShot(5000, self.enable_play_button)
            return
        # --- FIM DA ALTERAÇÃO ---

        executables = self.game_manager.get_executables_for_game(self.game_data['id'])
        if not executables:
            self.main_window_ref.show_message_box("Erro", "Este jogo não tem um executável configurado.", "warning")
            return
        
        executable_path = executables[0]['path']
        try:
            if executable_path.startswith("steam://"):
                logging.info(f"Iniciando jogo da Steam via protocolo: {executable_path}")
                webbrowser.open(executable_path)
                self.game_manager.update_last_played(self.game_data['id'])
                self.load_game_data(self.game_manager.get_game_by_id(self.game_data['id']))
                self.play_button.setEnabled(False)
                self.play_button.setText("INICIANDO...")
                QTimer.singleShot(5000, self.enable_play_button)
            elif os.path.exists(executable_path):
                logging.info(f"Iniciando executável local: {executable_path}")
                result, data = self.game_launcher.launch_game(self.game_data, executable_path)
                if isinstance(result, str) and result == "error": self.main_window_ref.show_message_box("Erro ao Iniciar", data, "warning")
                elif isinstance(result, str) and result == "running": self.main_window_ref.show_message_box("Aviso", "Este jogo já está em execução.", "info")
                else: self.main_window_ref.start_tracking_game(result, data)
            else:
                logging.error(f"Caminho do executável não encontrado: {executable_path}")
                self.main_window_ref.show_message_box("Erro", f"O arquivo executável não foi encontrado em:\n{executable_path}", "error")
        except Exception as e:
            logging.error(f"Erro ao tentar iniciar o jogo em '{executable_path}': {e}")
            self.main_window_ref.show_message_box("Erro", f"Ocorreu um erro inesperado ao iniciar o jogo:\n{e}", "error")

    def enable_play_button(self):
        """Função chamada pelo QTimer para reabilitar o botão principal."""
        self.play_button.setEnabled(True)
        # Recarrega os dados para garantir que o texto do botão esteja correto
        self.load_game_data(self.game_data)

    def _create_stat_widget(self, icon_path, title_text, value_text):
        stat_widget = QWidget(); stat_widget.setObjectName("StatItem")
        stat_layout = QHBoxLayout(stat_widget); stat_layout.setContentsMargins(10, 8, 10, 8); stat_layout.setSpacing(10)
        icon_label = QLabel(); icon_label.setObjectName("StatIcon")
        if os.path.exists(icon_path): icon_label.setPixmap(QPixmap(icon_path))
        icon_label.setFixedSize(QSize(24, 24)); icon_label.setScaledContents(True)
        text_layout = QVBoxLayout(); text_layout.setSpacing(0)
        title_label = QLabel(title_text.upper()); title_label.setObjectName("StatTitle")
        value_label = QLabel(value_text); value_label.setObjectName("StatValue")
        text_layout.addWidget(title_label); text_layout.addWidget(value_label)
        stat_layout.addWidget(icon_label); stat_layout.addLayout(text_layout)
        return stat_widget

    def load_game_data(self, game_data):
        self.game_data = game_data
        
        # --- INÍCIO DA ALTERAÇÃO ---
        # Atualiza o texto e o ícone do botão com base no status do jogo
        is_installed = self.game_data.get("status", "UNINSTALLED") == "INSTALLED"
        if is_installed:
            self.play_button.setText("▶ JOGAR")
            self.play_button.setIcon(QIcon()) # Remove o ícone se houver
        else:
            self.play_button.setText(" INSTALAR")
            self.play_button.setIcon(QIcon("assets/icons/download.svg"))
            self.play_button.setIconSize(QSize(18, 18))
        # --- FIM DA ALTERAÇÃO ---

        bg_path_raw = self.game_data.get("background_path") or self.game_data.get("image_path")
        cover_path_raw = self.game_data.get("image_path")
        bg_path_abs = get_absolute_path(bg_path_raw)
        if bg_path_abs and os.path.exists(bg_path_abs):
            self.background_pixmap = QPixmap(bg_path_abs)
        else:
            self.background_pixmap = None
        self.update() 
        self.title_label.setText(self.game_data.get("name", "Nome Indisponível"))
        cover_path_abs = get_absolute_path(cover_path_raw)
        if cover_path_abs and os.path.exists(cover_path_abs):
            pixmap = QPixmap(cover_path_abs)
            scaled_pixmap = pixmap.scaledToWidth(self.cover_label.maximumWidth(), Qt.TransformationMode.SmoothTransformation)
            self.cover_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            self.cover_label.setMinimumSize(0, 0)
            self.cover_label.setPixmap(scaled_pixmap)
            self.cover_label.adjustSize()
        else:
            self.cover_label.setText("Sem Capa")
            self.cover_label.setFixedSize(self.cover_label.maximumWidth(), int(self.cover_label.maximumWidth() * 1.5))
        is_favorite = self.game_data.get("favorite", False)
        self.fav_button.setIcon(QIcon("assets/icons/star.svg"))
        self.fav_button.setText(" Favorito" if is_favorite else " Favoritar")
        self.fav_button.setChecked(is_favorite)
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()
        playtime_seconds = self.game_data.get("playtime_local", 0) or 0
        playtime_hours = playtime_seconds / 3600
        playtime_widget = self._create_stat_widget("assets/icons/clock.svg", "Horas Jogadas", f"{playtime_hours:.1f}h")
        self.stats_layout.addWidget(playtime_widget)
        last_play_str = "Nunca"
        last_play_timestamp = self.game_data.get('last_played_timestamp')
        if last_play_timestamp:
            try:
                last_play_dt = datetime.fromtimestamp(last_play_timestamp)
                last_play_str = last_play_dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                last_play_str = "Data Inválida"
        last_played_widget = self._create_stat_widget("assets/icons/calendar.svg", "Última Vez", last_play_str)
        self.stats_layout.addWidget(last_played_widget)
        source = self.game_data.get('source', 'local')
        platform_icon_path = f"assets/icons/platform/{source.lower()}.svg"
        if not os.path.exists(platform_icon_path):
            platform_icon_path = "assets/icons/platform/local.svg"
        platform_widget = self._create_stat_widget(platform_icon_path, "Plataforma", source.upper())
        self.stats_layout.addWidget(platform_widget)
        self.stats_layout.addStretch()
        self.summary_text.setText(self.game_data.get("summary", "Nenhuma descrição disponível."))
        while self.genres_layout.count():
            item = self.genres_layout.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()
        genres_data = self.game_data.get("genres", "") or ""
        genres_list = genres_data.split(',') if isinstance(genres_data, str) else genres_data
        for genre_text in genres_list:
            if genre_text and genre_text.strip():
                genre_label = QLabel(genre_text.strip().upper()); genre_label.setObjectName("GenreTag")
                self.genres_layout.addWidget(genre_label)
        self.genres_layout.addStretch()

    def _toggle_favorite(self):
        self.game_manager.toggle_favorite(self.game_data['id'])
        updated_game_data = self.game_manager.get_game_by_id(self.game_data["id"])
        self.load_game_data(updated_game_data)
        self.main_window_ref.refresh_views()

    def _edit_game(self):
        dialog = GameEditDialog(self.game_data['id'], self.game_manager, self.main_window_ref)
        if dialog.exec():
            updated_game_data = self.game_manager.get_game_by_id(self.game_data["id"])
            if updated_game_data:
                self.load_game_data(updated_game_data)
            self.main_window_ref.refresh_views()

    def _delete_game(self):
        reply = self.main_window_ref.show_message_box("Confirmar Exclusão", f"Tem certeza que deseja excluir '{self.game_data['name']}'?","question", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.game_manager.delete_game(self.game_data['id'])
            self.back_clicked.emit()
