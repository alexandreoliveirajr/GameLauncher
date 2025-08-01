# core/game_manager.py

import os
import logging
import sqlite3
from datetime import datetime
from core.database import get_db_connection

class GameManager:
    def __init__(self):
        """O GameManager agora não carrega mais um arquivo, 
           ele simplesmente prepara-se para interagir com o banco de dados."""
        pass # Nenhuma inicialização de dados em memória é necessária

    def _game_from_row(self, row):
        """Converte uma linha do banco de dados para um dicionário Python."""
        if not row:
            return None
        game = dict(row)
        game['paths'] = self._get_executables_for_game(game['id'])
        game['tags'] = self._get_tags_for_game(game['id'])
        return game

    def _get_tags_for_game(self, game_id):
        """Busca todas as tags para um determinado ID de jogo."""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT t.name FROM tags t
            JOIN game_tags gt ON t.id = gt.tag_id
            WHERE gt.game_id = ?
        """, (game_id,)).fetchall()
        conn.close()
        return [row['name'] for row in rows]

    def _get_executables_for_game(self, game_id):
        """Busca todos os executáveis para um determinado ID de jogo."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT path, display_name FROM executables WHERE game_id = ?", (game_id,))
        executables = [{"path": row["path"], "display_name": row["display_name"]} for row in cursor.fetchall()]
        conn.close()
        return executables
    
    def _get_base_game_query_fields(self, alias=None):
        """Retorna a string de campos base, opcionalmente com um alias de tabela."""
        fields = [
            "id", "name", "source", "app_id", "igdb_id", "summary", "genres", 
            "release_date", "cover_url", "screenshot_urls", 
            "image_path as image", "background_path as background", 
            "header_path", "favorite", "total_playtime", "last_play_time"
        ]
        
        if alias:
            # Adiciona o prefixo "alias." a cada campo
            return ", ".join([f"{alias}.{field}" for field in fields])
        else:
            return ", ".join(fields)

    def add_game(self, name, paths, image_path=None, background_path=None, header_path=None, tags=None, source='local', app_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # A instrução INSERT com 6 colunas
            cursor.execute("""
                INSERT INTO games (name, source, app_id, image_path, background_path, header_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, source, app_id, image_path, background_path, header_path))
            
            game_id = cursor.lastrowid

            for exe in paths:
                cursor.execute("""
                    INSERT INTO executables (game_id, path, display_name)
                    VALUES (?, ?, ?)
                """, (game_id, exe['path'], exe['display_name']))
            
            conn.commit()
            logging.info(f"Jogo '{name}' adicionado ao banco de dados com ID {game_id}.")
            return True

        except sqlite3.IntegrityError:
            logging.warning(f"Tentativa de adicionar um jogo com executável duplicado: {paths}")
            conn.rollback()
            return False
            
        finally:
            conn.close()

    def update_game(self, old_game_data, new_game_data):
        game_id = old_game_data['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- LÓGICA DE GÊNEROS CORRIGIDA ---
        genres_value = new_game_data.get('genres')

        # Se 'genres' não veio nos dados novos, tenta pegar dos dados antigos
        if genres_value is None:
            genres_value = old_game_data.get('genres')

        # Agora, processa o valor que encontramos
        if isinstance(genres_value, list):
            # Se for uma lista (veio do IGDB), junta em uma string
            genres_to_save = ",".join(genres_value)
        elif isinstance(genres_value, str):
            # Se já for uma string (veio do DB), usa como está
            genres_to_save = genres_value
        else:
            # Se for None ou outro tipo, salva como string vazia para evitar erros
            genres_to_save = ""

        cursor.execute("""
            UPDATE games SET
                name = ?, image_path = ?, background_path = ?, header_path = ?, source = ?,
                summary = ?, genres = ?, release_date = ?, igdb_id = ?
            WHERE id = ?
        """, (
            new_game_data.get('name', old_game_data.get('name')),
            new_game_data.get('image', old_game_data.get('image')),
            new_game_data.get('background', old_game_data.get('background')),
            new_game_data.get('header', old_game_data.get('header')),
            new_game_data.get('source', old_game_data.get('source')),
            new_game_data.get('summary', old_game_data.get('summary')),
            genres_to_save,  # Usa nossa variável segura
            new_game_data.get('release_date', old_game_data.get('release_date')),
            new_game_data.get('igdb_id', old_game_data.get('igdb_id')),
            game_id
        ))

        # Deleta os executáveis antigos e insere os novos
        cursor.execute("DELETE FROM executables WHERE game_id = ?", (game_id,))
        for exe in new_game_data.get('paths', []):
            cursor.execute("""
                INSERT INTO executables (game_id, path, display_name) VALUES (?, ?, ?)
            """, (game_id, exe['path'], exe['display_name']))
        

        # Deleta as associações de tags antigas
        cursor.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))

        # Processa e insere as novas tags
        tags_list = new_game_data.get("tags", [])
        for tag_name in tags_list:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row['id']
                cursor.execute("INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)", (game_id, tag_id))

        conn.commit()
        conn.close()
        logging.info(f"Jogo ID {game_id} atualizado.")

        return True

    def delete_game(self, game_to_delete):
        game_id = game_to_delete['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
            cursor.execute("DELETE FROM executables WHERE game_id = ?", (game_id,))
            cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
            conn.commit()
            logging.info(f"Jogo ID {game_id} ('{game_to_delete['name']}') e seus dados associados foram deletados.")
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao deletar o jogo ID {game_id}: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_games(self):
        """Busca todos os jogos com todos os campos relevantes."""
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        rows = conn.execute(f"SELECT {fields} FROM games ORDER BY name COLLATE NOCASE ASC").fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]


    def get_game_by_id(self, game_id):
        """Busca um único jogo pelo seu ID no banco de dados com todos os campos."""
        if not game_id:
            return None
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        row = conn.execute(f"SELECT {fields} FROM games WHERE id = ?", (game_id,)).fetchone()
        conn.close()
        return self._game_from_row(row)

    def get_filtered_games(self, search_text, tag=None, sort_by="Nome (A-Z)"):
        conn = get_db_connection()
        fields = self._get_base_game_query_fields(alias='g')
        
        query = f"""
            SELECT DISTINCT {fields}
            FROM games g
            LEFT JOIN game_tags gt ON g.id = gt.game_id
            LEFT JOIN tags t ON gt.tag_id = t.id
        """
        
        conditions = []
        params = []

        if search_text:
            conditions.append("g.name LIKE ?")
            params.append(f"%{search_text}%")
        
        if tag:
            conditions.append("t.name = ?")
            params.append(tag)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        if sort_by == "Nome (A-Z)":
            query += " ORDER BY g.name COLLATE NOCASE ASC"
        elif sort_by == "Mais Jogado":
            query += " ORDER BY g.total_playtime DESC"
        elif sort_by == "Jogado Recentemente":
            query += " ORDER BY g.last_play_time DESC"
            
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]

    def get_all_unique_tags(self):
        """Busca todas as tags únicas existentes no banco de dados."""
        conn = get_db_connection()
        rows = conn.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE ASC").fetchall()
        conn.close()
        return [row['name'] for row in rows]

    def get_favorite_games(self):
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        rows = conn.execute(f"SELECT {fields} FROM games WHERE favorite = 1 ORDER BY name COLLATE NOCASE ASC").fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]
        
    def get_recent_games(self):
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        rows = conn.execute(f"SELECT {fields} FROM games WHERE last_play_time IS NOT NULL ORDER BY last_play_time DESC").fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]

    def toggle_favorite(self, game):
        game_id = game['id']
        new_fav_status = 1 if not game.get('favorite', False) else 0
        
        conn = get_db_connection()
        conn.execute("UPDATE games SET favorite = ? WHERE id = ?", (new_fav_status, game_id))
        conn.commit()
        conn.close()

    def add_playtime(self, game_to_update, seconds_played):
        game_id = game_to_update['id']
        current_playtime = game_to_update.get('total_playtime', 0) or 0
        new_total_playtime = current_playtime + seconds_played

        conn = get_db_connection()
        conn.execute("UPDATE games SET total_playtime = ? WHERE id = ?", (new_total_playtime, game_id))
        conn.commit()
        conn.close()
        logging.info(f"Adicionado {seconds_played}s para {game_to_update['name']}. Total: {new_total_playtime}s")

    def record_recent_play(self, game):
        game_id = game['id']
        now_iso = datetime.now().isoformat()
        
        conn = get_db_connection()
        conn.execute("UPDATE games SET last_play_time = ? WHERE id = ?", (now_iso, game_id))
        conn.commit()
        conn.close()

    def get_all_executable_paths(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT path FROM executables").fetchall()
        conn.close()
        return {os.path.normcase(row['path']) for row in rows}

    def get_most_common_genre(self):
        """Calcula o gênero mais comum entre todos os jogos na biblioteca."""
        from collections import Counter

        all_games = self.get_all_games()
        if not all_games:
            return "N/A"

        genre_list = []
        for game in all_games:
            # Pega os gêneros, que podem ser 'None' ou uma string "Ação, RPG"
            genres_str = game.get('genres')
            if genres_str and isinstance(genres_str, str):
                # Adiciona cada gênero individualmente à lista
                genre_list.extend([genre.strip() for genre in genres_str.split(',')])

        if not genre_list:
            return "N/A"

        # Conta a ocorrência de cada gênero e retorna o mais comum
        most_common = Counter(genre_list).most_common(1)
        return most_common[0][0]