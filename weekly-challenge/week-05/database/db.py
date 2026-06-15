import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "test.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            config_index INTEGER NOT NULL,
            temperature REAL NOT NULL,
            top_k INTEGER,
            repetition_penalty REAL NOT NULL,
            max_new_tokens INTEGER NOT NULL,
            generated_text TEXT NOT NULL,
            elapsed_time REAL NOT NULL,
            tokens_per_sec REAL NOT NULL,
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
    """)
    conn.commit()
    conn.close()
