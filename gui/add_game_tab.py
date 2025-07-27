# gui/add_game_tab.py

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QFormLayout, QGroupBox, QInputDialog
)
from PyQt6.QtCore import Qt

class AddGameTab(QWidget):
    def __init__(self, game_manager, main_window_ref):
        super().__init__()
        self.game_manager = game_manager
        self.main_window_ref = main_window_ref
        self.current_paths = []
        self._setup_ui()

    # O método _setup_ui já está correto da sua última versão, não precisa mudar.
    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label = QLabel("Adicionar Novo Jogo")
        
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do jogo (obrigatório)")
       
        form_layout.addRow("Nome:", self.name_input)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("RPG, Indie, Ação... (separadas por vírgula)")
        
        form_layout.addRow("Tags (Opcional):", self.tags_input)
        paths_group_box = QGroupBox("Caminhos dos Executáveis")
        self.paths_layout = QVBoxLayout()
        paths_group_box.setLayout(self.paths_layout)
        form_layout.addRow(paths_group_box)
        add_path_button = QPushButton("Adicionar Executável")
        add_path_button.clicked.connect(self._add_executable_path)
        form_layout.addRow(add_path_button)
        remove_path_button = QPushButton("Remover Executável Selecionado")
        remove_path_button.clicked.connect(self._remove_executable_path)
        form_layout.addRow(remove_path_button)
        self.image_path_label = QLabel("Nenhuma imagem selecionada")
        image_button = QPushButton("Selecionar Imagem de Capa")
        image_button.clicked.connect(lambda: self._select_file_dialog(self.image_path_label, "image"))
        form_layout.addRow(image_button)
        self.background_path_label = QLabel("Nenhum fundo selecionado")
        background_button = QPushButton("Selecionar Imagem de Fundo")
        background_button.clicked.connect(lambda: self._select_file_dialog(self.background_path_label, "background"))
        form_layout.addRow(background_button)
        main_layout.addLayout(form_layout)
        add_game_button = QPushButton("Adicionar Jogo à Biblioteca")
        add_game_button.clicked.connect(self._add_game)
        main_layout.addWidget(add_game_button, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        self.setLayout(main_layout)
        self._refresh_paths_display()

    # --- MÉTODO CORRIGIDO E MELHORADO ---
    def _add_executable_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Executável", "", "Executables (*.exe *.bat *.sh);;All Files (*)")
        if not file_path:
            return

        normalized_path = os.path.normcase(file_path)

        # 1. Verifica se o executável já está na lista DESTE JOGO
        if any(os.path.normcase(d['path']) == normalized_path for d in self.current_paths):
            self.main_window_ref.show_message_box("Aviso", "Este executável já foi adicionado para este jogo.", "warning")
            return

        # 2. VERIFICAÇÃO PROATIVA: Verifica se o executável já existe EM TODA A BIBLIOTECA
        existing_paths_in_db = self.game_manager.get_all_executable_paths()
        if normalized_path in existing_paths_in_db:
            self.main_window_ref.show_message_box(
                "Executável já Existe",
                "Este executável já pertence a outro jogo na sua biblioteca.",
                "warning"
            )
            return

        # Se passou em todas as verificações, adiciona
        if not self.name_input.text().strip():
            filename = os.path.basename(file_path)
            game_name, _ = os.path.splitext(filename)
            self.name_input.setText(game_name)

        display_name, ok = QInputDialog.getText(self, "Nome de Exibição", "Digite um nome para este executável:", QLineEdit.EchoMode.Normal, os.path.basename(file_path))
        if ok and display_name.strip():
            self.current_paths.append({"path": file_path, "display_name": display_name.strip()})
            self._refresh_paths_display()
        elif ok:
            self.main_window_ref.show_message_box("Aviso", "O nome de exibição não pode ser vazio.", "warning")

    # ... (_remove_executable_path e _refresh_paths_display permanecem os mesmos) ...
    def _remove_executable_path(self):
        if not self.current_paths: self.main_window_ref.show_message_box("Aviso", "Não há executáveis para remover.", "warning"); return
        items = [f"{d['display_name']} - {os.path.basename(d['path'])}" for d in self.current_paths]
        item, ok = QInputDialog.getItem(self, "Remover Executável", "Selecione o executável para remover:", items, 0, False)
        if ok and item:
            for idx, d in enumerate(self.current_paths):
                if f"{d['display_name']} - {os.path.basename(d['path'])}" == item:
                    del self.current_paths[idx]; break
            self._refresh_paths_display()

    def _refresh_paths_display(self):
        for i in reversed(range(self.paths_layout.count())):
            widget = self.paths_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
        if self.current_paths:
            for d in self.current_paths:
                lbl = QLabel(f"• {d['display_name']} — {os.path.basename(d['path'])}")

        else:
            lbl = QLabel("(Nenhum executável adicionado)"); 

    def _select_file_dialog(self, label_widget, file_type):
        filter_str = "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"; file_path, _ = QFileDialog.getOpenFileName(self, f"Selecionar {file_type.replace('_', ' ')}", "", filter_str)
        if file_path:
            if file_type == "image": self.image_path = file_path
            elif file_type == "background": self.background_path = file_path
            label_widget.setText(os.path.basename(file_path)); 

    # --- MÉTODO CORRIGIDO ---
    def _add_game(self):
        game_name = self.name_input.text().strip()
        if not game_name or not self.current_paths:
            self.main_window_ref.show_message_box("Erro de Validação", "O nome do jogo e ao menos um executável são obrigatórios.", "warning")
            return

        image_path = getattr(self, 'image_path', None)
        background_path = getattr(self, 'background_path', None)
        
        tags_text = self.tags_input.text().strip()
        tags_list = [tag.strip() for tag in tags_text.split(',')] if tags_text else []
        
        success = self.game_manager.add_game(game_name, self.current_paths, image_path, background_path, tags=tags_list)

        if success:
            self.main_window_ref.show_message_box("Sucesso", f"Jogo '{game_name}' adicionado com sucesso!")
            
            # Limpa o formulário
            self.name_input.clear(); self.tags_input.clear(); self.current_paths = []
            self._refresh_paths_display()
            self.image_path_label.setText("Nenhuma imagem selecionada"); 
            self.background_path_label.setText("Nenhum fundo selecionado"); 
            if hasattr(self, 'image_path'): delattr(self, 'image_path')
            if hasattr(self, 'background_path'): delattr(self, 'background_path')
        else:
            self.main_window_ref.show_message_box("Jogo Duplicado", "Não foi possível adicionar o jogo. Um dos executáveis selecionados já existe na sua biblioteca.", "warning")
        
        self.main_window_ref.refresh_views()