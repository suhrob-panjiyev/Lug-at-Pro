import sqlite3
from pathlib import Path

BOT_DB_PATH = Path("data/classroom.db")
BOT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_bot_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(BOT_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn