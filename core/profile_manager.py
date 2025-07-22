# core/profile_manager.py

import json
import os
from datetime import datetime

class ProfileManager:
    def __init__(self, data_file="profile.json"):
        self.data_file = data_file
        self.data = self._load_profile()

    def _load_profile(self):
        if not os.path.exists(self.data_file):
            default_profile = {
                "username": "Player1",
                "bio": "Bem-vindo ao meu launcher!",
                "avatar_path": None,
                "background_path": None,
                "showcased_favorite_id": None,
                "creation_date": datetime.now().isoformat() # ADICIONADO
            }
            self.save_profile(default_profile)
            return default_profile
        
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    return self._load_profile()
                data = json.loads(content)
                data.setdefault("showcased_favorite_id", None)
                data.setdefault("creation_date", datetime.now().isoformat()) # ADICIONADO
                return data
        except (json.JSONDecodeError, TypeError):
            print(f"Erro ao ler o arquivo de perfil {self.data_file}. Um novo será criado.")
            os.rename(self.data_file, self.data_file + ".bak")
            return self._load_profile()

    def get_data(self):
        return self.data

    def save_profile(self, profile_data):
        self.data = profile_data
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)