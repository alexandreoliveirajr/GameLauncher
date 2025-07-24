# core/database.py

import sqlite3
import logging

DATABASE_FILE = "launcher.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Permite acessar colunas pelo nome
    return conn

def initialize_database():
    """Cria as tabelas iniciais do banco de dados, se elas não existirem."""
    logging.info("Verificando e inicializando o banco de dados...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela de Jogos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        source TEXT DEFAULT 'local', -- De onde o jogo veio (ex: 'steam', 'epic', 'local')
        app_id TEXT, -- ID específico da loja (ex: Steam AppID)
        image_path TEXT,
        background_path TEXT,
        header_path TEXT,
        favorite INTEGER NOT NULL DEFAULT 0, -- 0 para False, 1 para True
        total_playtime INTEGER NOT NULL DEFAULT 0, -- Em segundos
        last_play_time TEXT -- Data no formato ISO
    );
    """)

    # Tabela para os executáveis (um jogo pode ter vários)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS executables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        path TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
    );
    """)
    
    # Tabela para dados do perfil (será uma tabela de uma linha só)
    # No futuro podemos transformar em uma tabela de chave-valor.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY CHECK (id = 1), -- Garante que só haja uma linha
        username TEXT DEFAULT 'Player1',
        bio TEXT DEFAULT 'Adicione sua bio aqui...',
        avatar_path TEXT,
        background_path TEXT,
        showcased_favorite_id INTEGER,
        creation_date TEXT
    );
    """)

    #Tabelas para tags
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_tags (
        game_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (game_id, tag_id),
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    );
    """)

    # Tabela para caminhos de launchers populares
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY NOT NULL,
        value TEXT
    );
    """)

    conn.commit()
    conn.close()
    logging.info("Banco de dados inicializado com sucesso.")