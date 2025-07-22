# game_launcher/core/game_launcher.py

import subprocess
import os
import sys

class GameLauncher:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.running_processes = {} 

    # --- MÉTODO MODIFICADO ---
    def launch_game(self, game_to_launch, game_path):
        """
        Tenta lançar um jogo. Agora recebe o objeto do jogo diretamente.
        """
        # A busca pelo jogo foi removida, pois ele agora é passado como argumento.

        if not os.path.exists(game_path):
            return ("error", f"Arquivo não encontrado: {game_path}")

        proc = self.running_processes.get(game_path)
        if proc and proc.poll() is None:
            return ("running", None)

        try:
            # Esta é a parte que lança o jogo
            log_file_path = os.path.join(os.path.dirname(game_path), f"{os.path.basename(game_path).lower()}_launch_log.txt")
            with open(log_file_path, "w") as log_file:
                process = subprocess.Popen(
                    [game_path],
                    cwd=os.path.dirname(game_path), # <--- ESTÁ AQUI
                    stdout=log_file, # <--- E AQUI
                    stderr=log_file, # <--- E AQUI
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
            self.running_processes[game_path] = process
            
            if game_to_launch:
                self.game_manager.record_recent_play(game_to_launch)
                
            # Retorna o processo e o dicionário do jogo que foi fornecido
            return (process, game_to_launch)
            
        except FileNotFoundError:
            return ("error", f"Executável não encontrado. Verifique o caminho: {game_path}")
        except Exception as e:
            return ("error", f"Ocorreu um erro ao tentar iniciar o jogo: {e}")