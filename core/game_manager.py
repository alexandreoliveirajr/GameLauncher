# game_launcher/core/game_manager.py

import json
import os
import shutil
from datetime import datetime

class GameManager:
    def __init__(self, data_file="games_data.json"):
        self.data_file = data_file
        self.games = self._load_games()

    def _load_games(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content:
                        return []
                    games_data = json.loads(content)
                    
                    needs_saving = False
                    for game in games_data:
                        if isinstance(game.get("paths"), str):
                            game["paths"] = [{"path": game["paths"], "display_name": os.path.basename(game["paths"])}]
                        
                        if "recent_play_time" in game and isinstance(game["recent_play_time"], str):
                            try:
                                game["recent_play_time"] = datetime.fromisoformat(game["recent_play_time"])
                            except (ValueError, TypeError):
                                game["recent_play_time"] = None
                        
                        game.setdefault("total_playtime", 0)

                        if "id" not in game or not game["id"]:
                            game["id"] = self._generate_id()
                            needs_saving = True

                    if needs_saving:
                        print("Salvando novas IDs geradas para jogos antigos...")
                        self._save_games_data(games_data)

                    return games_data
            except (json.JSONDecodeError, TypeError) as e:
                print(f"ERRO: O arquivo '{self.data_file}' parece estar corrompido. Erro: {e}")
                backup_file = self.data_file + ".bak"
                shutil.copy(self.data_file, backup_file)
                print(f"Um backup foi criado em: '{backup_file}'. Iniciando com uma biblioteca vazia.")
                return []
        return []

    def _save_games_data(self, games_list):
        games_to_save = []
        for game in games_list:
            game_copy = game.copy()
            if "recent_play_time" in game_copy and isinstance(game_copy["recent_play_time"], datetime):
                game_copy["recent_play_time"] = game_copy["recent_play_time"].isoformat()
            games_to_save.append(game_copy)

        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(games_to_save, f, indent=4)
    
    def _save_games(self):
        self._save_games_data(self.games)

    def add_game(self, name, paths, image_path=None, background_path=None):
        new_game = {
            "id": self._generate_id(),
            "name": name,
            "paths": paths,
            "image": image_path,
            "background": background_path,
            "favorite": False,
            "recent_play_time": None,
            "total_playtime": 0
        }
        self.games.append(new_game)
        self._save_games()
        return True

    def update_game(self, old_game_data, new_game_data):
        try:
            index = next(i for i, game in enumerate(self.games) if game["id"] == old_game_data["id"])
            
            self.games[index]["name"] = new_game_data.get("name", self.games[index]["name"])
            self.games[index]["paths"] = new_game_data.get("paths", self.games[index]["paths"])
            self.games[index]["image"] = new_game_data.get("image", self.games[index]["image"])
            self.games[index]["background"] = new_game_data.get("background", self.games[index]["background"])
            
            self._save_games()
            return True
        except StopIteration:
            print(f"Jogo com ID {old_game_data['id']} não encontrado para atualização.")
            return False

    def delete_game(self, game_to_delete):
        original_len = len(self.games)
        self.games = [game for game in self.games if game["id"] != game_to_delete["id"]]
        if len(self.games) < original_len:
            self._save_games()
            return True
        return False

    # --- MÉTODO MODIFICADO ---
    def get_all_games(self):
        # Retorna a lista de jogos ordenada pelo nome (case-insensitive)
        return sorted(self.games, key=lambda game: game['name'].lower())

    def get_game_by_id(self, game_id):
        return next((game for game in self.games if game["id"] == game_id), None)

    def _generate_id(self):
        return str(int(datetime.now().timestamp() * 1000))

    def toggle_favorite(self, game):
        game["favorite"] = not game.get("favorite", False)
        self._save_games()

    # --- MÉTODO MODIFICADO ---
    def get_favorite_games(self):
        # Filtra os jogos favoritos
        favorite_games = [game for game in self.games if game.get("favorite", False)]
        # Retorna a lista de favoritos ordenada pelo nome
        return sorted(favorite_games, key=lambda game: game['name'].lower())

    def record_recent_play(self, game):
        game["recent_play_time"] = datetime.now()
        self._save_games()
    
    def add_playtime(self, game_to_update, seconds_played):
        game_to_update["total_playtime"] = game_to_update.get("total_playtime", 0) + seconds_played
        print(f"Adicionado {seconds_played}s para {game_to_update['name']}. Total: {game_to_update['total_playtime']}s")
        self._save_games()

    # Este método continua ordenado por data, como deve ser.
    def get_recent_games(self):
        for g in self.games:
            if isinstance(g.get("recent_play_time"), str):
                try: g["recent_play_time"] = datetime.fromisoformat(g["recent_play_time"])
                except: g["recent_play_time"] = None
        return sorted(
            [game for game in self.games if game.get("recent_play_time")],
            key=lambda x: x.get("recent_play_time", datetime.min),
            reverse=True
        )

    # --- MÉTODO MODIFICADO ---
    def get_filtered_games(self, search_text):
        if not search_text:
            # Se a busca estiver vazia, retorna todos os jogos já ordenados
            return self.get_all_games()
        
        search_text_lower = search_text.lower()
        # Filtra os jogos
        filtered_games = [
            game for game in self.games 
            if search_text_lower in game["name"].lower() 
            or any(search_text_lower in d["display_name"].lower() for d in game.get("paths", []))
        ]
        # Retorna a lista filtrada também ordenada pelo nome
        return sorted(filtered_games, key=lambda game: game['name'].lower())
