# core/settings_manager.py

import json
import os

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.settings = self._load_settings()

    def _load_settings(self):
        if not os.path.exists(self.settings_file):
            print("Arquivo de configurações não encontrado. Criando um novo.")
            default_settings = {
                "steam_common_path": None,
                "epic_games_path": None
            }
            self._save_settings(default_settings)
            return default_settings
        
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, TypeError):
            print("Erro ao ler o arquivo de configurações. Um novo será criado.")
            os.rename(self.settings_file, self.settings_file + ".bak")
            return self._load_settings()

    def _save_settings(self, settings_data):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=4)

    def get_setting(self, key):
        return self.settings.get(key)

    def save_setting(self, key, value):
        self.settings[key] = value
        self._save_settings(self.settings)