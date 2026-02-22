import os
import sqlite3
from pathlib import Path
from typing import Union
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import psycopg

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "classroom.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _is_postgres() -> bool:
    return DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")


def get_conn() -> Any:
    """
    Bot DB connection.
    - If DATABASE_URL set => Postgres (schema: bot)
    - Else => SQLite (data/classroom.db)
    """
    if _is_postgres():
        import psycopg
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("SET search_path TO bot;")
        conn.commit()
        return conn

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db() -> None:
    conn = get_conn()

    # --------- POSTGRES ----------
    if _is_postgres():
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS bot;")
            cur.execute("SET search_path TO bot;")

            cur.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                group_id BIGINT NOT NULL,
                teacher_id BIGINT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id BIGSERIAL PRIMARY KEY,
                class_id BIGINT,
                user_id BIGINT,
                full_name TEXT,
                joined_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(class_id, user_id)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id BIGSERIAL PRIMARY KEY,
                class_id BIGINT NOT NULL,
                n_questions INT NOT NULL,
                deadline_hhmm TEXT,
                deadline_at TIMESTAMPTZ,
                is_active INT DEFAULT 1,
                questions_json TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id BIGSERIAL PRIMARY KEY,
                assignment_id BIGINT NOT NULL,
                class_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                full_name TEXT,
                score INT NOT NULL,
                total INT NOT NULL,
                pct DOUBLE PRECISION NOT NULL,
                finished_at TIMESTAMPTZ DEFAULT NOW(),
                is_late INT DEFAULT 0,
                answers_json TEXT,
                UNIQUE(assignment_id, user_id)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS xp_log (
                id BIGSERIAL PRIMARY KEY,
                class_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                full_name TEXT,
                xp INT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS weekly_runs (
                id BIGSERIAL PRIMARY KEY,
                class_id BIGINT NOT NULL,
                week_start TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(class_id, week_start)
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id BIGSERIAL PRIMARY KEY,
                class_id BIGINT NOT NULL,
                assignment_id BIGINT NOT NULL,
                status TEXT DEFAULT 'pending',
                error TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                sent_at TIMESTAMPTZ
            );
            """)

        conn.commit()
        conn.close()
        return

    # --------- SQLITE ----------
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        group_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        user_id INTEGER,
        full_name TEXT,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(class_id, user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        n_questions INTEGER NOT NULL,
        deadline_hhmm TEXT,
        is_active INTEGER DEFAULT 1,
        questions_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        pct REAL NOT NULL,
        finished_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(assignment_id, user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS xp_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        xp INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS weekly_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        week_start TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(class_id, week_start)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        assignment_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        error TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        sent_at TEXT
    )
    """)

    conn.commit()
    conn.close()