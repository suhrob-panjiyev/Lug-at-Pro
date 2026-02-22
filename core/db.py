import os
import sqlite3
from pathlib import Path
from typing import Union
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

DB_PATH = Path("data/app.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _is_postgres() -> bool:
    return DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")


def get_conn() -> Any: 
    """
    Web DB connection.
    - If DATABASE_URL set => Postgres (schema: web)
    - Else => SQLite (data/app.db)
    """
    if _is_postgres():
        import psycopg
        conn = psycopg.connect(DATABASE_URL)
        # ✅ make web tables visible with same names
        with conn.cursor() as cur:
            cur.execute("SET search_path TO web;")
        conn.commit()
        return conn

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    conn = get_conn()

    # --------- POSTGRES ----------
    if _is_postgres():
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS web;")
            cur.execute("SET search_path TO web;")

            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                phone TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_login_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                en TEXT NOT NULL,
                uz TEXT NOT NULL,
                UNIQUE(user_id, en, uz)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                mode TEXT NOT NULL,
                test_id BIGINT,
                level TEXT,
                score INT NOT NULL,
                total INT NOT NULL,
                pct DOUBLE PRECISION NOT NULL,
                ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """)

        conn.commit()
        conn.close()
        return

    # --------- SQLITE ----------
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_login_at TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        en TEXT NOT NULL,
        uz TEXT NOT NULL,
        UNIQUE(user_id, en, uz),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mode TEXT NOT NULL,
        test_id INTEGER,
        level TEXT,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        pct REAL NOT NULL,
        ts TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()