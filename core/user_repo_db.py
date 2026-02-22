from __future__ import annotations

from datetime import datetime
from core.db import get_conn


# -------------------------
# Helpers
# -------------------------
def _is_postgres(conn) -> bool:
    # psycopg connection: module name odatda "psycopg" bo‘ladi
    mod = conn.__class__.__module__.lower()
    return "psycopg" in mod or "psycopg2" in mod


def _ph(conn) -> str:
    # placeholder: postgres -> %s, sqlite -> ?
    return "%s" if _is_postgres(conn) else "?"


def _row_to_dict(cur, row):
    """
    sqlite: row_factory=sqlite3.Row bo‘lsa dict(row) ishlaydi
    psycopg: row tuple bo‘lishi mumkin -> cursor.description dan nomlarini olamiz
    """
    if row is None:
        return None

    try:
        return dict(row)  # sqlite3.Row yoki dict-like bo‘lsa
    except Exception:
        cols = [d[0] for d in (cur.description or [])]
        return dict(zip(cols, row))


# -------------------------
# Repo
# -------------------------
def upsert_user(first_name: str, last_name: str, phone: str) -> dict:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    conn = get_conn()
    cur = conn.cursor()
    p = _ph(conn)

    # Universal upsert (SQLite >= 3.24 va Postgres’da bor)
    sql = f"""
    INSERT INTO users (phone, first_name, last_name, created_at, last_login_at)
    VALUES ({p}, {p}, {p}, {p}, {p})
    ON CONFLICT(phone) DO UPDATE SET
        first_name = excluded.first_name,
        last_name = excluded.last_name,
        last_login_at = excluded.last_login_at
    """

    cur.execute(sql, (phone, first_name, last_name, now, now))
    conn.commit()

    # Qayta o‘qib dict qilib qaytaramiz (ham sqlite, ham postgres)
    cur.execute(f"SELECT * FROM users WHERE phone = {p}", (phone,))
    u = _row_to_dict(cur, cur.fetchone())

    conn.close()
    return u


def get_user_by_phone(phone: str):
    conn = get_conn()
    cur = conn.cursor()
    p = _ph(conn)

    cur.execute(f"SELECT * FROM users WHERE phone = {p}", (phone,))
    row = cur.fetchone()

    data = _row_to_dict(cur, row)
    conn.close()
    return data