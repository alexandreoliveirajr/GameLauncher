# core/game_manager.py

import os
import logging
import sqlite3
import time
from datetime import datetime
from core.database import get_db_connection
from core.artwork_manager import download_steam_artwork

class GameManager:
    def __init__(self):
        pass

    def _game_from_row(self, row):
        if not row:
            return None
        game = dict(row)
        game['paths'] = self.get_executables_for_game(game['id'])
        game['tags'] = self._get_tags_for_game(game['id'])
        return game

    def _get_tags_for_game(self, game_id):
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT t.name FROM tags t
            JOIN game_tags gt ON t.id = gt.tag_id
            WHERE gt.game_id = ?
        """, (game_id,)).fetchall()
        conn.close()
        return [row['name'] for row in rows]

    def get_executables_for_game(self, game_id):
        conn = get_db_connection()
        try:
            executables = conn.execute("SELECT path, display_name FROM executables WHERE game_id = ?", (game_id,)).fetchall()
            return [dict(row) for row in executables]
        finally:
            conn.close()
    
    def _get_base_game_query_fields(self, alias=None):
        fields = [
            "id", "name", "source", "app_id", "igdb_id", "summary", "genres", 
            "release_date", "cover_url", "screenshot_urls", 
            "image_path", "background_path", 
            "header_path", "favorite", "playtime_local", "last_played_timestamp", "status",
            "playtime_steam"
        ]
        
        if alias:
            return ", ".join([f"{alias}.{field}" for field in fields])
        else:
            return ", ".join(fields)

    def add_game(self, name, paths, image_path=None, background_path=None, header_path=None, tags=None, source='local', app_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
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
        genres_value = new_game_data.get('genres')
        if genres_value is None:
            genres_value = old_game_data.get('genres')
        if isinstance(genres_value, list):
            genres_to_save = ",".join(genres_value)
        elif isinstance(genres_value, str):
            genres_to_save = genres_value
        else:
            genres_to_save = ""
        image_to_save = new_game_data.get('image_path') or new_game_data.get('image') or old_game_data.get('image_path')
        background_to_save = new_game_data.get('background_path') or new_game_data.get('background') or old_game_data.get('background_path')
        header_to_save = new_game_data.get('header_path') or new_game_data.get('header') or old_game_data.get('header_path')
        cursor.execute("""
            UPDATE games SET
                name = ?, image_path = ?, background_path = ?, header_path = ?, source = ?,
                summary = ?, genres = ?, release_date = ?, igdb_id = ?
            WHERE id = ?
        """, (
            new_game_data.get('name', old_game_data.get('name')),
            image_to_save, background_to_save, header_to_save,
            new_game_data.get('source', old_game_data.get('source')),
            new_game_data.get('summary', old_game_data.get('summary')),
            genres_to_save,
            new_game_data.get('release_date', old_game_data.get('release_date')),
            new_game_data.get('igdb_id', old_game_data.get('igdb_id')),
            game_id
        ))
        cursor.execute("DELETE FROM executables WHERE game_id = ?", (game_id,))
        for exe in new_game_data.get('paths', []):
            cursor.execute("INSERT INTO executables (game_id, path, display_name) VALUES (?, ?, ?)", (game_id, exe['path'], exe['display_name']))
        cursor.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
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

    def delete_game(self, game_id):
        conn = get_db_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
            conn.commit()
            logging.info(f"Jogo ID {game_id} e seus dados associados foram deletados.")
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao deletar o jogo ID {game_id}: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_games(self):
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        rows = conn.execute(f"SELECT {fields} FROM games ORDER BY name COLLATE NOCASE ASC").fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]

    def get_game_by_id(self, game_id):
        if not game_id: return None
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        row = conn.execute(f"SELECT {fields} FROM games WHERE id = ?", (game_id,)).fetchone()
        conn.close()
        return self._game_from_row(row)

    # --- INÍCIO DA ALTERAÇÃO ---
    def get_filtered_games(self, search_text, tag=None, sort_by="Nome (A-Z)", status_filter="Todos"):
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

        # Adiciona a nova condição para o filtro de status
        if status_filter == "Instalados":
            conditions.append("g.status = ?")
            params.append("INSTALLED")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        if sort_by == "Nome (A-Z)": query += " ORDER BY g.name COLLATE NOCASE ASC"
        elif sort_by == "Mais Jogado": query += " ORDER BY g.playtime_local DESC"
        elif sort_by == "Jogado Recentemente": query += " ORDER BY g.last_played_timestamp DESC"
            
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]

    def get_all_unique_tags(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE ASC").fetchall()
        conn.close()
        return [row['name'] for row in rows]

    def get_favorite_games(self, status_filter="Todos"):
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        
        query = f"SELECT {fields} FROM games WHERE favorite = 1"
        params = []

        # Adiciona a condição de status também aos favoritos
        if status_filter == "Instalados":
            query += " AND status = ?"
            params.append("INSTALLED")
            
        query += " ORDER BY name COLLATE NOCASE ASC"
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]
    # --- FIM DA ALTERAÇÃO ---
        
    def get_recent_games(self):
        conn = get_db_connection()
        fields = self._get_base_game_query_fields()
        rows = conn.execute(f"SELECT {fields} FROM games WHERE last_played_timestamp IS NOT NULL ORDER BY last_played_timestamp DESC").fetchall()
        conn.close()
        return [self._game_from_row(row) for row in rows]

    def toggle_favorite(self, game_id):
        conn = get_db_connection()
        current_status = conn.execute("SELECT favorite FROM games WHERE id = ?", (game_id,)).fetchone()['favorite']
        new_fav_status = 1 if not current_status else 0
        conn.execute("UPDATE games SET favorite = ? WHERE id = ?", (new_fav_status, game_id))
        conn.commit()
        conn.close()

    def add_playtime(self, game_id, seconds_played):
        conn = get_db_connection()
        current_playtime = conn.execute("SELECT playtime_local FROM games WHERE id = ?", (game_id,)).fetchone()['playtime_local'] or 0
        new_playtime_local = current_playtime + seconds_played
        conn.execute("UPDATE games SET playtime_local = ? WHERE id = ?", (new_playtime_local, game_id))
        conn.commit()
        conn.close()
        logging.info(f"Adicionado {seconds_played}s para o jogo ID {game_id}. Total: {new_playtime_local}s")

    def update_last_played(self, game_id):
        conn = get_db_connection()
        try:
            current_timestamp = int(time.time())
            conn.execute("UPDATE games SET last_played_timestamp = ? WHERE id = ?", (current_timestamp, game_id))
            conn.commit()
        finally:
            conn.close()

    def get_all_executable_paths(self):
        conn = get_db_connection()
        rows = conn.execute("SELECT path FROM executables").fetchall()
        conn.close()
        return {os.path.normcase(row['path']) for row in rows}

    def get_most_common_genre(self):
        from collections import Counter
        all_games = self.get_all_games()
        if not all_games: return "N/A"
        genre_list = []
        for game in all_games:
            genres_str = game.get('genres')
            if genres_str and isinstance(genres_str, str):
                genre_list.extend([genre.strip() for genre in genres_str.split(',')])
        if not genre_list: return "N/A"
        most_common = Counter(genre_list).most_common(1)
        return most_common[0][0]

    def add_or_update_steam_game(self, app_id, name, install_dir, status):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            game = cursor.execute("SELECT id, image_path FROM games WHERE source = 'steam' AND app_id = ?", (app_id,)).fetchone()
            if game:
                game_id = game['id']
                cursor.execute("UPDATE games SET status = ?, install_dir = ?, name = ? WHERE id = ?", (status, install_dir, name, game_id))
            else:
                cursor.execute("INSERT INTO games (name, source, app_id, install_dir, status) VALUES (?, 'steam', ?, ?, ?)", (name, app_id, install_dir, status))
                game_id = cursor.lastrowid
            if game_id:
                executable_path = f"steam://run/{app_id}"
                exec_exists = cursor.execute("SELECT id FROM executables WHERE game_id = ? AND path = ?", (game_id, executable_path)).fetchone()
                if not exec_exists:
                    cursor.execute("INSERT INTO executables (game_id, path, display_name) VALUES (?, ?, ?)", (game_id, executable_path, "Iniciar via Steam"))
            conn.commit()
            if game_id and (not game or not game['image_path']):
                logging.info(f"Buscando artes para o jogo '{name}' (AppID: {app_id})...")
                artwork_paths = download_steam_artwork(app_id)
                if artwork_paths:
                    self.update_game_artwork(game_id, app_id, **artwork_paths)
        except sqlite3.Error as e:
            logging.error(f"Erro ao adicionar/atualizar jogo da Steam (AppID: {app_id}): {e}")
        finally:
            conn.close()

    def update_uninstalled_steam_games(self, installed_app_ids):
        if not installed_app_ids:
            query = "UPDATE games SET status = 'UNINSTALLED' WHERE source = 'steam'"
            params = []
        else:
            placeholder = ', '.join('?' for _ in installed_app_ids)
            query = f"UPDATE games SET status = 'UNINSTALLED' WHERE source = 'steam' AND app_id NOT IN ({placeholder})"
            params = list(installed_app_ids)
        conn = get_db_connection()
        try:
            conn.execute(query, params)
            conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar status de jogos desinstalados da Steam: {e}")
        finally:
            conn.close()

    def update_game_artwork(self, game_id, app_id, image_path=None, background_path=None, header_path=None):
        conn = get_db_connection()
        try:
            conn.execute(
                """UPDATE games SET 
                   app_id = ?, image_path = ?, background_path = ?, header_path = ?
                   WHERE id = ?""",
                (app_id, image_path, background_path, header_path, game_id)
            )
            conn.commit()
            logging.info(f"Artes atualizadas para o jogo ID {game_id} com o AppID {app_id}.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar artes para o jogo ID {game_id}: {e}")
        finally:
            conn.close()

    def sync_full_steam_library(self, owned_games_list):
        conn = get_db_connection()
        cursor = conn.cursor()
        added_count = 0
        updated_count = 0
        cursor.execute("SELECT app_id FROM games WHERE source = 'steam'")
        existing_app_ids = {row['app_id'] for row in cursor.fetchall()}
        for game_data in owned_games_list:
            app_id = str(game_data.get('appid'))
            name = game_data.get('name')
            playtime_minutes = game_data.get('playtime_forever', 0)
            if not app_id or not name:
                continue
            if app_id not in existing_app_ids:
                logging.info(f"Novo jogo da biblioteca encontrado: '{name}'. Adicionando...")
                cursor.execute(
                    """INSERT INTO games (name, source, app_id, status, playtime_steam)
                       VALUES (?, 'steam', ?, 'UNINSTALLED', ?)""",
                    (name, app_id, playtime_minutes)
                )
                game_id = cursor.lastrowid
                conn.commit()
                artwork_paths = download_steam_artwork(app_id)
                if artwork_paths:
                    self.update_game_artwork(game_id, app_id, **artwork_paths)
                added_count += 1
                existing_app_ids.add(app_id)
            else:
                cursor.execute(
                    "UPDATE games SET playtime_steam = ? WHERE app_id = ? AND source = 'steam'",
                    (playtime_minutes, app_id)
                )
                updated_count += 1
        conn.commit()
        conn.close()
        logging.info(f"Sincronização da biblioteca completa: {added_count} novos jogos adicionados, {updated_count} jogos atualizados.")
