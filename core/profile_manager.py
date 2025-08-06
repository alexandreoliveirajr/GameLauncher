# core/profile_manager.py

import logging
from datetime import datetime
from core.database import get_db_connection

class ProfileManager:
    def __init__(self):
        """Inicializa o ProfileManager, garantindo que a linha de perfil exista no DB."""
        self._initialize_profile()

    def _initialize_profile(self):
        """Garante que a linha única de perfil (id=1) exista na tabela."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Adiciona a coluna 'bio' e seu valor padrão à instrução INSERT
        cursor.execute("""
            INSERT OR IGNORE INTO profile (id, username, bio, creation_date) 
            VALUES (?, ?, ?, ?)
        """, (1, 'Player1', 'Adicione sua bio aqui...', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_data(self):
        """Busca os dados do perfil do banco de dados e retorna como um dicionário."""
        conn = get_db_connection()
        # fetchone() busca a única linha que corresponde à consulta
        row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        conn.close()
        
        if row:
            return dict(row)
        else:
            # Esta é uma salvaguarda caso a linha seja deletada manualmente.
            logging.error("A linha de perfil não foi encontrada no banco de dados. Recriando.")
            self._initialize_profile()
            return self.get_data()

    def save_profile(self, profile_data):
        """Salva (atualiza) os dados do perfil no banco de dados."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE profile SET
                username = ?,
                bio = ?, 
                avatar_path = ?,
                background_path = ?,
                showcased_favorite_id = ?,
                real_name = ?,          -- NOVO CAMPO
                country_code = ?        -- NOVO CAMPO
            WHERE id = 1
        """, (
            profile_data.get('username'),
            profile_data.get('bio'),
            profile_data.get('avatar_path'),
            profile_data.get('background_path'),
            profile_data.get('showcased_favorite_id'),
            profile_data.get('real_name'),   # NOVO CAMPO
            profile_data.get('country_code') # NOVO CAMPO
        ))
        
        conn.commit()
        conn.close()
        logging.info("Dados do perfil salvos no banco de dados.")

    def update_steam_credentials(self, api_key, steam_id):
        """Salva a chave de API e o SteamID no banco de dados."""
        conn = get_db_connection()
        conn.execute(
            "UPDATE profile SET steam_api_key = ?, steam_id_64 = ? WHERE id = 1",
            (api_key, steam_id)
        )
        conn.commit()
        conn.close()