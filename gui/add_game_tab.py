# gui/add_game_tab.py

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QFormLayout, QGroupBox, QInputDialog
)
from PyQt5.QtCore import Qt

class AddGameTab(QWidget):
    def __init__(self, game_manager, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        self.current_paths = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Adicionar Novo Jogo")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px; color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do jogo (obrigatório)")
        self.name_input.setStyleSheet("background-color: #333; color: white; border: 1px solid #555; border-radius: 5px; padding: 8px;")
        form_layout.addRow("Nome:", self.name_input)

        paths_group_box = QGroupBox("Caminhos dos Executáveis")
        paths_group_box.setStyleSheet("color: white;")
        self.paths_layout = QVBoxLayout()
        paths_group_box.setLayout(self.paths_layout)
        form_layout.addRow(paths_group_box)

        add_path_button = QPushButton("Adicionar Executável")
        add_path_button.setStyleSheet("background-color: #555; color: white; border-radius: 5px; padding: 8px;")
        add_path_button.clicked.connect(self._add_executable_path)
        form_layout.addRow(add_path_button)

        remove_path_button = QPushButton("Remover Executável Selecionado")
        remove_path_button.setStyleSheet("background-color: #555; color: white; border-radius: 5px; padding: 8px;")
        remove_path_button.clicked.connect(self._remove_executable_path)
        form_layout.addRow(remove_path_button)

        self.image_path_label = QLabel("Nenhuma imagem selecionada")
        self.image_path_label.setStyleSheet("color: #aaa; font-style: italic;")
        image_button = QPushButton("Selecionar Imagem de Capa")
        image_button.setStyleSheet("background-color: #555; color: white; border-radius: 5px; padding: 8px;")
        image_button.clicked.connect(lambda: self._select_file_dialog(self.image_path_label, "image"))
        form_layout.addRow(image_button)

        self.background_path_label = QLabel("Nenhum fundo selecionado")
        self.background_path_label.setStyleSheet("color: #aaa; font-style: italic;")
        background_button = QPushButton("Selecionar Imagem de Fundo")
        background_button.setStyleSheet("background-color: #555; color: white; border-radius: 5px; padding: 8px;")
        background_button.clicked.connect(lambda: self._select_file_dialog(self.background_path_label, "background"))
        form_layout.addRow(background_button)

        main_layout.addLayout(form_layout)

        add_game_button = QPushButton("Adicionar Jogo à Biblioteca")
        add_game_button.setStyleSheet("background-color: #3c3; color: black; font-weight: bold; border-radius: 8px; padding: 12px; margin-top: 20px;")
        add_game_button.clicked.connect(self._add_game)
        main_layout.addWidget(add_game_button, alignment=Qt.AlignCenter)

        main_layout.addStretch()
        self.setLayout(main_layout)

        self._refresh_paths_display()

    def _add_executable_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Executável", "", "Executables (*.exe *.bat *.sh);;All Files (*)")
        if file_path:
            # --- LÓGICA ADICIONADA AQUI ---
            # Se o campo de nome estiver vazio, preenche com o nome do arquivo
            if not self.name_input.text().strip():
                # Pega apenas o nome do arquivo, sem o caminho
                filename = os.path.basename(file_path)
                # Remove a extensão (ex: .exe) para obter o nome limpo
                game_name, _ = os.path.splitext(filename)
                self.name_input.setText(game_name)
            # --- FIM DA LÓGICA ADICIONADA ---

            display_name, ok = QInputDialog.getText(self, "Nome de Exibição", "Digite um nome para este executável:", QLineEdit.Normal, os.path.basename(file_path))
            if ok and display_name.strip():
                if not any(d['path'] == file_path for d in self.current_paths):
                    self.current_paths.append({"path": file_path, "display_name": display_name.strip()})
                    self._refresh_paths_display()
                else:
                    self.main_window_ref.show_message_box("Aviso", "Este executável já foi adicionado.", "warning")
            elif ok:
                 self.main_window_ref.show_message_box("Aviso", "O nome de exibição não pode ser vazio.", "warning")

    def _remove_executable_path(self):
        if not self.current_paths:
            self.main_window_ref.show_message_box("Aviso", "Não há executáveis para remover.", "warning")
            return

        items = [f"{d['display_name']} - {os.path.basename(d['path'])}" for d in self.current_paths]
        item, ok = QInputDialog.getItem(self, "Remover Executável", "Selecione o executável para remover:", items, 0, False)

        if ok and item:
            for idx, d in enumerate(self.current_paths):
                if f"{d['display_name']} - {os.path.basename(d['path'])}" == item:
                    del self.current_paths[idx]
                    break
            self._refresh_paths_display()

    def _refresh_paths_display(self):
        for i in reversed(range(self.paths_layout.count())):
            widget = self.paths_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.current_paths:
            for d in self.current_paths:
                lbl = QLabel(f"• {d['display_name']} — {os.path.basename(d['path'])}")
                lbl.setStyleSheet("color: white;")
                lbl.setWordWrap(True)
                self.paths_layout.addWidget(lbl)
        else:
            lbl = QLabel("(Nenhum executável adicionado)")
            lbl.setStyleSheet("color: #777; font-style: italic;")
            self.paths_layout.addWidget(lbl)

    def _select_file_dialog(self, label_widget, file_type):
        filter_str = "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Selecionar {file_type.replace('_', ' ')}", "", filter_str)
        if file_path:
            if file_type == "image":
                self.image_path = file_path
            elif file_type == "background":
                self.background_path = file_path
            label_widget.setText(os.path.basename(file_path))
            label_widget.setStyleSheet("color: white;")
        else:
            pass

    def _add_game(self):
        game_name = self.name_input.text().strip()
        if not game_name:
            self.main_window_ref.show_message_box("Erro", "O nome do jogo é obrigatório.", "warning")
            return
        
        if not self.current_paths:
            self.main_window_ref.show_message_box("Erro", "É necessário adicionar ao menos um executável.", "warning")
            return

        image_path = getattr(self, 'image_path', None)
        background_path = getattr(self, 'background_path', None)
        
        self.game_manager.add_game(game_name, self.current_paths, image_path, background_path)
        
        self.main_window_ref.show_message_box("Sucesso", f"Jogo '{game_name}' adicionado com sucesso!")
        
        self.name_input.clear()
        self.current_paths = []
        self._refresh_paths_display()
        self.image_path_label.setText("Nenhuma imagem selecionada")
        self.image_path_label.setStyleSheet("color: #aaa; font-style: italic;")
        self.background_path_label.setText("Nenhum fundo selecionado")
        self.background_path_label.setStyleSheet("color: #aaa; font-style: italic;")
        
        if hasattr(self, 'image_path'):
            delattr(self, 'image_path')
        if hasattr(self, 'background_path'):
            delattr(self, 'background_path')
        
        self.main_window_ref.refresh_views()