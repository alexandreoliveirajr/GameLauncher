# core/settings_manager.py

import logging
from core.database import get_db_connection

class SettingsManager:
    def __init__(self):
        """O SettingsManager agora interage diretamente com a tabela 'settings' do DB."""
        pass

    def get_setting(self, key):
        """Busca o valor de uma configuração no banco de dados pela sua chave."""
        conn = get_db_connection()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        
        if row:
            return row['value']
        else:
            # Retorna None se a configuração ainda não foi definida
            return None

    def save_setting(self, key, value):
        """Salva (insere ou atualiza) uma configuração no banco de dados."""
        conn = get_db_connection()
        
        # INSERT OR REPLACE é um comando SQLite muito útil.
        # Se a 'key' não existir, ele insere uma nova linha.
        # Se a 'key' já existir, ele atualiza o 'value' da linha existente.
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        
        conn.commit()
        conn.close()
        logging.info(f"Configuração salva: {key} = {value}")