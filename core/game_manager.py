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

        # Atualiza a tabela 'games'
        cursor.execute("""
            UPDATE games SET
                name = ?, image_path = ?, background_path = ?, header_path = ?
            WHERE id = ?
        """, (
            new_game_data.get('name', old_game_data['name']),
            new_game_data.get('image', old_game_data.get('image')),
            new_game_data.get('background', old_game_data.get('background')),
            new_game_data.get('header', old_game_data.get('header')),
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
            # Insere a tag na tabela 'tags' se ela não existir, e ignora se já existir
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            # Pega o ID da tag (seja a que foi inserida ou a que já existia)
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                tag_id = tag_row['id']
                # Cria a associação na tabela 'game_tags'
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
            # Deleta explicitamente as associações de tags
            cursor.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))

            # Deleta explicitamente os executáveis
            cursor.execute("DELETE FROM executables WHERE game_id = ?", (game_id,))

            # Finalmente, deleta o jogo principal
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
        """Busca todos os jogos, usado para contagens e verificações internas."""
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT id, name, image_path as image, background_path as background, header_path,
                   favorite, total_playtime, last_play_time
            FROM games ORDER BY name COLLATE NOCASE ASC
        """).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_game_by_id(self, game_id):
        """Busca um único jogo pelo seu ID no banco de dados."""
        if not game_id:
            return None
        conn = get_db_connection()
        row = conn.execute("""
            SELECT id, name, image_path as image, background_path as background, header_path,
                   favorite, total_playtime, last_play_time
            FROM games WHERE id = ?
        """, (game_id,)).fetchone()
        conn.close()
        return self._game_from_row(row)

    def get_filtered_games(self, search_text, tag=None, sort_by="Nome (A-Z)"):
        conn = get_db_connection()
        query = """
            SELECT id, name, image_path as image, background_path as background, header_path,
                   favorite, total_playtime, last_play_time
            FROM games
        """
        params = []
        if search_text:
            query += " WHERE name LIKE ?"
            params.append(f"%{search_text}%")
        
        if sort_by == "Nome (A-Z)":
            query += " ORDER BY name COLLATE NOCASE ASC"
        elif sort_by == "Mais Jogado":
            query += " ORDER BY total_playtime DESC"
        elif sort_by == "Jogado Recentemente":
            query += " ORDER BY last_play_time DESC"
            
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
        rows = conn.execute("""
            SELECT id, name, image_path as image, background_path as background, header_path,
                   favorite, total_playtime, last_play_time
            FROM games WHERE favorite = 1 ORDER BY name COLLATE NOCASE ASC
        """).fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]
        
    def get_recent_games(self):
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT id, name, image_path as image, background_path as background, header_path,
                   favorite, total_playtime, last_play_time
            FROM games WHERE last_play_time IS NOT NULL ORDER BY last_play_time DESC
        """).fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]

    def toggle_favorite(self, game):
        game_id = game['id']
        # Converte o valor booleano para 0 ou 1
        new_fav_status = 1 if not game.get('favorite', False) else 0
        
        conn = get_db_connection()
        conn.execute("UPDATE games SET favorite = ? WHERE id = ?", (new_fav_status, game_id))
        conn.commit()
        conn.close()

    def add_playtime(self, game_to_update, seconds_played):
        game_id = game_to_update['id']
        # Garante que o playtime atual é um número
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
        """Retorna um set com todos os caminhos de executáveis já existentes no DB,
           TODOS NORMALIZADOS para comparação case-insensitive."""
        conn = get_db_connection()
        rows = conn.execute("SELECT path FROM executables").fetchall()
        conn.close()
        return {os.path.normcase(row['path']) for row in rows}