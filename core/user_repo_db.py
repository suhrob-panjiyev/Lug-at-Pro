from datetime import datetime
from core.db import get_conn


def upsert_user(first_name: str, last_name: str, phone: str) -> dict:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    row = cur.fetchone()

    if row:
        cur.execute(
            "UPDATE users SET first_name=?, last_name=?, last_login_at=? WHERE phone=?",
            (first_name, last_name, now, phone),
        )
    else:
        cur.execute(
            "INSERT INTO users (phone, first_name, last_name, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)",
            (phone, first_name, last_name, now, now),
        )

    conn.commit()

    cur.execute("SELECT * FROM users WHERE phone=?", (phone,))
    u = dict(cur.fetchone())
    conn.close()
    return u
def get_user_by_phone(phone: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE phone=?", (phone,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None