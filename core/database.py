# core/database.py

import sqlite3
import logging
import time

DATABASE_FILE = "launcher.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return conn

def _table_exists(cursor, table_name):
    """Verifica se uma tabela existe no banco de dados."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def _column_exists(cursor, table_name, column_name):
    """Verifica se uma coluna existe em uma tabela."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row['name'] for row in cursor.fetchall()]
    return column_name in columns

def initialize_database():
    """Cria as tabelas iniciais do banco de dados, se elas não existirem."""
    logging.info("Verificando e inicializando o banco de dados...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de Jogos com a nova estrutura completa
    if not _table_exists(cursor, "games"):
        cursor.execute("""
        CREATE TABLE games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            app_id TEXT,
            igdb_id TEXT,
            summary TEXT,
            genres TEXT,
            release_date TEXT,
            cover_url TEXT,
            screenshot_urls TEXT,
            image_path TEXT,
            background_path TEXT,
            header_path TEXT,
            favorite INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'UNINSTALLED',
            install_dir TEXT,
            playtime_steam INTEGER NOT NULL DEFAULT 0,
            playtime_local INTEGER NOT NULL DEFAULT 0,
            last_played_timestamp INTEGER
        );
        """)

    # Tabela para os executáveis (um jogo pode ter vários)
    if not _table_exists(cursor, "executables"):
        cursor.execute("""
        CREATE TABLE executables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            path TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
        );
        """)
    
    # Tabela para dados do perfil
    if not _table_exists(cursor, "profile"):
        cursor.execute("""
        CREATE TABLE profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT DEFAULT 'Player1',
            bio TEXT DEFAULT 'Adicione sua bio aqui...',
            avatar_path TEXT,
            background_path TEXT,
            showcased_favorite_id INTEGER,
            creation_date TEXT,
            real_name TEXT,
            country_code TEXT,
            steam_api_key TEXT,
            steam_id_64 TEXT
        );
        """)

    # Tabelas para tags
    if not _table_exists(cursor, "tags"):
        cursor.execute("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """)

    if not _table_exists(cursor, "game_tags"):
        cursor.execute("""
        CREATE TABLE game_tags (
            game_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (game_id, tag_id),
            FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        );
        """)

    # Tabela para configurações
    if not _table_exists(cursor, "settings"):
        cursor.execute("""
        CREATE TABLE settings (
            key TEXT PRIMARY KEY NOT NULL,
            value TEXT
        );
        """)

    conn.commit()
    conn.close()
    logging.info("Banco de dados inicializado com sucesso.")
    
    update_database_schema()
    migrate_data_if_needed()

def update_database_schema():
    """Adiciona novas colunas a tabelas existentes de forma segura para compatibilidade."""
    logging.info("Verificando e atualizando o schema do banco de dados...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    schema_updates = {
        "profile": [
            ("real_name", "TEXT"),
            ("country_code", "TEXT"),
            ("steam_api_key", "TEXT"),
            ("steam_id_64", "TEXT")
        ]
    }

    for table, columns in schema_updates.items():
        for column_name, column_type in columns:
            if not _column_exists(cursor, table, column_name):
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type};")
                    logging.info(f"Coluna '{column_name}' adicionada à tabela '{table}'.")
                except sqlite3.OperationalError as e:
                    logging.error(f"Não foi possível adicionar a coluna {column_name} à tabela {table}: {e}")

    conn.commit()
    conn.close()
    logging.info("Verificação de schema concluída.")

def migrate_data_if_needed():
    """Executa a migração da tabela 'games' se colunas antigas ainda existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # A migração só é necessária se a coluna antiga 'total_playtime' existir.
    if _column_exists(cursor, "games", "total_playtime"):
        logging.info("Detectada estrutura antiga da tabela 'games'. Iniciando migração...")
        try:
            # 1. Renomear a tabela antiga
            cursor.execute("ALTER TABLE games RENAME TO games_old;")

            # 2. Criar a nova tabela 'games' com a estrutura correta
            cursor.execute("""
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                app_id TEXT,
                igdb_id TEXT,
                summary TEXT,
                genres TEXT,
                release_date TEXT,
                cover_url TEXT,
                screenshot_urls TEXT,
                image_path TEXT,
                background_path TEXT,
                header_path TEXT,
                favorite INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'INSTALLED', -- Jogos existentes estavam instalados
                install_dir TEXT, -- Será preenchido pelo scanner
                playtime_steam INTEGER NOT NULL DEFAULT 0,
                playtime_local INTEGER NOT NULL DEFAULT 0,
                last_played_timestamp INTEGER
            );
            """)

            # 3. Copiar os dados da tabela antiga para a nova, mapeando as colunas
            # Nota: last_played_timestamp é deixado como NULL pois a conversão de TEXT para INTEGER é complexa
            cursor.execute("""
            INSERT INTO games (
                id, name, source, app_id, igdb_id, summary, genres, release_date,
                cover_url, screenshot_urls, image_path, background_path, header_path,
                favorite, playtime_local
            )
            SELECT
                id, name, source, app_id, igdb_id, summary, genres, release_date,
                cover_url, screenshot_urls, image_path, background_path, header_path,
                favorite, total_playtime
            FROM games_old;
            """)
            
            # 4. Remover a tabela antiga
            cursor.execute("DROP TABLE games_old;")
            
            conn.commit()
            logging.info("Tabela 'games' migrada com sucesso para a nova estrutura.")

        except sqlite3.Error as e:
            logging.error(f"Ocorreu um erro durante a migração da tabela 'games': {e}")
            conn.rollback() # Desfaz as alterações em caso de erro
    else:
        logging.info("Nenhuma migração de dados necessária para a tabela 'games'.")

    conn.close()


# Ao executar este script diretamente, ele inicializa o banco de dados.
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    initialize_database()
