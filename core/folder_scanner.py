# core/folder_scanner.py

import os
import logging
import platform
import vdf

class SteamScanner:
    """
    Classe focada exclusivamente em encontrar e sincronizar jogos da Steam
    instalados localmente usando os arquivos de manifesto.
    """
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def _find_steam_library_paths(self):
        """Encontra todos os diretórios de biblioteca da Steam no sistema."""
        library_paths = set()
        default_path = ""

        if platform.system() == "Windows":
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
                default_path = winreg.QueryValueEx(key, "InstallPath")[0]
                winreg.CloseKey(key)
            except FileNotFoundError:
                logging.warning("Instalação da Steam não encontrada no registro do Windows.")
                return []
        elif platform.system() == "Linux":
            default_path = os.path.expanduser("~/.steam/steam")
        elif platform.system() == "Darwin":
            default_path = os.path.expanduser("~/Library/Application Support/Steam")
        
        if not os.path.isdir(default_path):
            logging.warning(f"Diretório padrão da Steam não encontrado em: {default_path}")
            return []

        main_library_path = os.path.join(default_path, "steamapps")
        if os.path.isdir(main_library_path):
            library_paths.add(main_library_path)

        library_folders_vdf = os.path.join(main_library_path, "libraryfolders.vdf")
        if os.path.exists(library_folders_vdf):
            try:
                with open(library_folders_vdf, 'r', encoding='utf-8') as f:
                    data = vdf.load(f)
                for key, value in data.get('libraryfolders', {}).items():
                    if isinstance(value, dict) and 'path' in value:
                        path = os.path.join(value['path'], "steamapps")
                        if os.path.isdir(path):
                            library_paths.add(path)
            except Exception as e:
                logging.error(f"Erro ao ler o arquivo libraryfolders.vdf: {e}")

        return list(library_paths)

    def _parse_acf_file(self, acf_path):
        """Extrai informações de um arquivo .acf."""
        try:
            with open(acf_path, 'r', encoding='utf-8') as f:
                data = vdf.load(f)
            app_state = data.get('AppState')
            if not app_state: return None
            return {
                'appid': app_state.get('appid'),
                'name': app_state.get('name'),
                'installdir': app_state.get('installdir')
            }
        except Exception as e:
            logging.error(f"Erro ao processar o arquivo ACF '{acf_path}': {e}")
            return None

    def sync_steam_games(self):
        """
        Sincroniza o banco de dados com os jogos da Steam instalados localmente.
        """
        logging.info("Iniciando sincronização de jogos da Steam...")
        library_paths = self._find_steam_library_paths()
        if not library_paths:
            logging.warning("Nenhuma biblioteca da Steam foi encontrada. Sincronização cancelada.")
            return

        installed_app_ids = set()
        for lib_path in library_paths:
            logging.info(f"Escaneando biblioteca da Steam em: {lib_path}")
            for filename in os.listdir(lib_path):
                if filename.startswith('appmanifest_') and filename.endswith('.acf'):
                    acf_path = os.path.join(lib_path, filename)
                    game_info = self._parse_acf_file(acf_path)
                    if game_info and game_info.get('appid'):
                        app_id = game_info['appid']
                        installed_app_ids.add(app_id)
                        install_dir = os.path.join(lib_path, 'common', game_info['installdir'])
                        self.game_manager.add_or_update_steam_game(
                            app_id=app_id, name=game_info['name'],
                            install_dir=install_dir, status='INSTALLED'
                        )
        logging.info(f"Encontrados {len(installed_app_ids)} jogos da Steam instalados.")
        self.game_manager.update_uninstalled_steam_games(installed_app_ids)
        logging.info("Sincronização da Steam concluída.")


class LocalGameScanner:
    """
    Escaneia pastas genéricas em busca de jogos locais (não-Steam).
    """
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.exclude_list = [
            "uninstall", "unins000", "setup", "redist", "dxsetup",
            "vcredist", "crashreport", "config", "settings", "launcher", "report"
        ]

    def _is_valid_exe(self, file_path, existing_paths):
        if os.path.normcase(file_path) in existing_paths:
            return False
        file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0].lower()
        return not any(excluded in file_name_no_ext for excluded in self.exclude_list)

    def _scan_subfolder(self, folder, existing_paths, is_deep_scan):
        potential_exes = []
        try:
            walk_target = os.walk(folder) if is_deep_scan else [(os.path.dirname(folder), [], [os.path.basename(folder)])]
            for root, _, files in walk_target:
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
            logging.warning(f"Permissão negada para acessar a pasta: {folder}")
            return None

        if potential_exes:
            main_exe = max(potential_exes, key=lambda x: x['size'])
            return {
                "name": os.path.splitext(os.path.basename(main_exe['path']))[0],
                "path": main_exe['path'],
                "source": "local"
            }
        return None

    def scan_folder(self, path, is_deep_scan=False):
        """Executa a varredura para jogos locais."""
        scan_type = "COMPLETA" if is_deep_scan else "RÁPIDA"
        logging.info(f"Iniciando varredura local {scan_type} em: {path}")
        found_games = []
        existing_paths = self.game_manager.get_all_executable_paths()

        try:
            subfolders = [f.path for f in os.scandir(path) if f.is_dir()]
        except (FileNotFoundError, PermissionError) as e:
            logging.error(f"Erro ao acessar '{path}': {e}")
            return []

        for folder in subfolders:
            game_data = self._scan_subfolder(folder, existing_paths, is_deep_scan)
            if game_data:
                found_games.append(game_data)
        
        logging.info(f"Varredura local {scan_type} concluída. {len(found_games)} potenciais jogos encontrados.")
        return found_games
