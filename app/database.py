import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "gamemate.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_connection() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            category TEXT NOT NULL,
            item_name TEXT NOT NULL,
            notes TEXT,
            source TEXT,
            game_version TEXT
        );
        CREATE TABLE IF NOT EXISTS account_characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            level INTEGER,
            build_json TEXT,
            imported_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
