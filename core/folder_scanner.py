# core/folder_scanner.py

import os
from core import steam_api # Importa nosso novo módulo

class FolderScanner:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.exclude_list = [
            "uninstall", "unins000", "setup", "redist", "dxsetup",
            "vcredist", "crashreport", "config", "settings", "launcher",
            "report"
        ]

    def _is_valid_exe(self, file_path, existing_paths):
        normalized_path = os.path.normcase(file_path)
        if normalized_path in existing_paths:
            return False
        
        file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0].lower()
        if any(excluded in file_name_no_ext for excluded in self.exclude_list):
            return False
            
        return True

    def _scan_subfolder(self, folder, existing_paths, is_deep_scan=False):
        """Lógica de varredura para uma única subpasta de jogo."""
        potential_exes = []

        try:
            if not is_deep_scan:
                # Busca Rápida: Apenas na raiz da pasta do jogo
                for item in os.scandir(folder):
                    if item.is_file() and item.name.lower().endswith('.exe'):
                        if self._is_valid_exe(item.path, existing_paths):
                            try:
                                size = item.stat().st_size
                                potential_exes.append({'path': item.path, 'size': size})
                            except FileNotFoundError:
                                continue
            else:
                # Busca Completa: Em todas as subpastas
                for root, _, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith('.exe'):
                            file_path = os.path.join(root, file)
                            if self._is_valid_exe(file_path, existing_paths):
                                try:
                                    size = os.path.getsize(file_path)
                                    potential_exes.append({'path': file_path, 'size': size})
                                except FileNotFoundError:
                                    continue
        except PermissionError:
            print(f"Permissão negada para acessar a pasta: {folder}")
            return None

        if potential_exes:
            main_exe = max(potential_exes, key=lambda x: x['size'])
            
            # Tenta encontrar a AppID da Steam para esta pasta
            app_id = steam_api.find_steam_app_id(folder)
            
            game_data = {
                "name": os.path.splitext(os.path.basename(main_exe['path']))[0],
                "path": main_exe['path'],
                "app_id": app_id # Adiciona a AppID se encontrada
            }
            return game_data
        
        return None

    def _run_scan(self, path, is_deep_scan):
        """Executa a varredura (rápida ou completa)."""
        scan_type = "COMPLETA" if is_deep_scan else "RÁPIDA"
        print(f"Iniciando varredura {scan_type} em: {path}")
        
        found_games = []
        existing_paths = {os.path.normcase(p['path']) for game in self.game_manager.get_all_games() for p in game.get('paths', [])}

        try:
            subfolders = [f.path for f in os.scandir(path) if f.is_dir()]
        except (FileNotFoundError, PermissionError) as e:
            print(f"Erro ao acessar '{path}': {e}")
            return []

        for folder in subfolders:
            game_data = self._scan_subfolder(folder, existing_paths, is_deep_scan)
            if game_data:
                found_games.append(game_data)
        
        print(f"Varredura {scan_type} concluída. {len(found_games)} novos jogos encontrados.")
        return found_games
    
    def scan_folder_simple(self, path):
        return self._run_scan(path, is_deep_scan=False)

    def scan_folder_deep(self, path):
        return self._run_scan(path, is_deep_scan=True)