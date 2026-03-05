from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.storage.db import get_conn

TZ = ZoneInfo("Asia/Samarkand")


def _is_psycopg_conn(conn) -> bool:
    return conn.__class__.__module__.startswith("psycopg")


# =========================
# Classes / Members
# =========================

def get_class_by_group(group_id: int):
    conn = get_conn()
    cur = conn.cursor()

    sql = (
        "SELECT id, name, group_id, teacher_id FROM classes WHERE group_id=%s ORDER BY id DESC LIMIT 1"
        if _is_psycopg_conn(conn)
        else
        "SELECT id, name, group_id, teacher_id FROM classes WHERE group_id=? ORDER BY id DESC LIMIT 1"
    )

    cur.execute(sql, (group_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_group_id_by_class(class_id: int) -> int | None:
    conn = get_conn()
    cur = conn.cursor()

    sql = "SELECT group_id FROM classes WHERE id=%s" if _is_psycopg_conn(conn) else "SELECT group_id FROM classes WHERE id=?"
    cur.execute(sql, (class_id,))
    row = cur.fetchone()

    conn.close()
    return int(row[0]) if row else None


def ensure_member(class_id: int, user_id: int, full_name: str) -> None:
    conn = get_conn()
    cur = conn.cursor()

    if _is_psycopg_conn(conn):
        cur.execute(
            """
            INSERT INTO members (class_id, user_id, full_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (class_id, user_id) DO NOTHING
            """,
            (class_id, user_id, full_name),
        )
    else:
        cur.execute(
            "INSERT OR IGNORE INTO members (class_id, user_id, full_name) VALUES (?, ?, ?)",
            (class_id, user_id, full_name),
        )

    conn.commit()
    conn.close()


def list_classes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, group_id FROM classes")
    rows = cur.fetchall()
    conn.close()
    return rows


# =========================
# Assignments
# =========================

def _parse_deadline_hhmm(deadline_hhmm: str | None) -> tuple[int, int] | None:
    if not deadline_hhmm:
        return None
    m = re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", str(deadline_hhmm).strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _deadline_at_for_today(deadline_hhmm: str | None) -> str | None:
    hhmm = _parse_deadline_hhmm(deadline_hhmm)
    if not hhmm:
        return None
    hh, mm = hhmm
    now = datetime.now(TZ)
    dl = datetime(now.year, now.month, now.day, hh, mm, 0, tzinfo=TZ)
    return dl.isoformat()


def create_assignment(class_id: int, n_questions: int, deadline_hhmm: str | None):
    dl_at = _deadline_at_for_today(deadline_hhmm)

    conn = get_conn()
    cur = conn.cursor()

    if _is_psycopg_conn(conn):
        # Postgres
        try:
            cur.execute(
                """
                INSERT INTO assignments (class_id, n_questions, deadline_hhmm, deadline_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (class_id, n_questions, deadline_hhmm, dl_at),
            )
            aid = cur.fetchone()[0]
        except Exception:
            cur.execute(
                """
                INSERT INTO assignments (class_id, n_questions, deadline_hhmm)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (class_id, n_questions, deadline_hhmm),
            )
            aid = cur.fetchone()[0]
    else:
        # SQLite
        try:
            cur.execute(
                "INSERT INTO assignments (class_id, n_questions, deadline_hhmm, deadline_at) VALUES (?, ?, ?, ?)",
                (class_id, n_questions, deadline_hhmm, dl_at),
            )
        except Exception:
            cur.execute(
                "INSERT INTO assignments (class_id, n_questions, deadline_hhmm) VALUES (?, ?, ?)",
                (class_id, n_questions, deadline_hhmm),
            )
        aid = cur.lastrowid

    conn.commit()
    conn.close()
    return aid


def get_active_assignment(class_id: int):
    conn = get_conn()
    cur = conn.cursor()

    sql = (
        "SELECT id, n_questions, deadline_hhmm FROM assignments WHERE class_id=%s AND is_active=1 ORDER BY id DESC LIMIT 1"
        if _is_psycopg_conn(conn)
        else
        "SELECT id, n_questions, deadline_hhmm FROM assignments WHERE class_id=? AND is_active=1 ORDER BY id DESC LIMIT 1"
    )

    cur.execute(sql, (class_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_assignment_questions(assignment_id: int, questions_payload: list) -> None:
    conn = get_conn()
    cur = conn.cursor()
    sql = (
        "UPDATE assignments SET questions_json=%s WHERE id=%s"
        if _is_psycopg_conn(conn)
        else
        "UPDATE assignments SET questions_json=? WHERE id=?"
    )
    cur.execute(sql, (json.dumps(questions_payload, ensure_ascii=False), assignment_id))
    conn.commit()
    conn.close()


import json
from bot.storage.db import get_conn

def get_assignment_questions(assignment_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT questions_json FROM assignments WHERE id=?", (int(assignment_id),))
    row = cur.fetchone()
    conn.close()

    if not row:
        return []

    qj = row["questions_json"] if hasattr(row, "keys") else row[0]
    if not qj:
        return []

    # ✅ 1) agar string bo'lsa JSON parse qilamiz
    if isinstance(qj, str):
        qj = qj.strip()
        try:
            qj = json.loads(qj)
        except Exception:
            return []

    # ✅ 2) Agar dict bo'lsa, ichidan "questions" ni olamiz
    # Siz create_assignment_web() da shunaqa saqlayapsiz:
    # fixed = {"n_questions":..., "seed":..., "questions": []}
    if isinstance(qj, dict):
        qj = qj.get("questions") or []

    # ✅ 3) Endi qj list bo'lishi kerak
    if not isinstance(qj, list):
        return []

    # ✅ 4) elementlar dict bo'lishi kerak
    out = []
    for item in qj:
        if isinstance(item, dict) and "en" in item and "uz" in item:
            out.append(item)

    return out

def _ensure_deadline_at(assignment_id: int) -> None:
    """If deadline_at is empty but deadline_hhmm exists, compute deadline_at from created_at date (SQLite side)."""
    conn = get_conn()
    cur = conn.cursor()

    # Bu helper asosan sqlite uchun kerak, postgresda deadline_at odatda bor bo‘ladi
    try:
        cur.execute("SELECT created_at, deadline_hhmm, deadline_at FROM assignments WHERE id=?", (assignment_id,))
    except Exception:
        conn.close()
        return

    row = cur.fetchone()
    if not row:
        conn.close()
        return

    created_at, deadline_hhmm, deadline_at = row
    if deadline_at or not deadline_hhmm:
        conn.close()
        return

    hhmm = _parse_deadline_hhmm(deadline_hhmm)
    if not hhmm:
        conn.close()
        return
    hh, mm = hhmm

    date_part = str(created_at).split(" ")[0].split("T")[0]
    try:
        y, mo, d = map(int, date_part.split("-"))
    except Exception:
        conn.close()
        return

    dl = datetime(y, mo, d, hh, mm, 0, tzinfo=TZ).isoformat()
    try:
        cur.execute("UPDATE assignments SET deadline_at=? WHERE id=?", (dl, assignment_id))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def is_assignment_late(assignment_id: int) -> bool:
    _ensure_deadline_at(assignment_id)

    conn = get_conn()
    cur = conn.cursor()

    sql = (
        "SELECT deadline_at FROM assignments WHERE id=%s AND is_active=1"
        if _is_psycopg_conn(conn)
        else
        "SELECT deadline_at FROM assignments WHERE id=? AND is_active=1"
    )
    try:
        cur.execute(sql, (assignment_id,))
    except Exception:
        conn.close()
        return False

    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return False

    try:
        dl = datetime.fromisoformat(row[0])
    except Exception:
        return False

    return datetime.now(TZ) > dl


# =========================
# Attempts
# =========================

def save_attempt(
    assignment_id: int,
    class_id: int,
    user_id: int,
    full_name: str,
    score: int,
    total: int,
    pct: float,
    *,
    is_late: int = 0,
    answers_json: str | None = None,
) -> None:
    conn = get_conn()
    cur = conn.cursor()

    if _is_psycopg_conn(conn):
        cur.execute(
            """
            INSERT INTO attempts
            (assignment_id, class_id, user_id, full_name, score, total, pct, is_late, answers_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (assignment_id, user_id)
            DO UPDATE SET
                full_name=EXCLUDED.full_name,
                score=EXCLUDED.score,
                total=EXCLUDED.total,
                pct=EXCLUDED.pct,
                is_late=EXCLUDED.is_late,
                answers_json=EXCLUDED.answers_json,
                finished_at=NOW()
            """,
            (assignment_id, class_id, user_id, full_name, score, total, pct, int(is_late), answers_json),
        )
    else:
        cur.execute(
            """
            INSERT OR REPLACE INTO attempts
            (assignment_id, class_id, user_id, full_name, score, total, pct, is_late, answers_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (assignment_id, class_id, user_id, full_name, score, total, pct, int(is_late), answers_json),
        )

    conn.commit()
    conn.close()


# =========================
# Weekly top helpers
# =========================

def week_start_date(dt: datetime) -> str:
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%Y-%m-%d")


def weekly_top3(class_id: int, days: int = 7):
    conn = get_conn()
    cur = conn.cursor()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    if _is_psycopg_conn(conn):
        cur.execute(
            """
            SELECT user_id, full_name, SUM(xp) as total
            FROM xp_log
            WHERE class_id=%s AND created_at::date >= %s::date
            GROUP BY user_id, full_name
            ORDER BY total DESC
            LIMIT 3
            """,
            (class_id, since),
        )
    else:
        cur.execute(
            """
            SELECT user_id, full_name, SUM(xp) as total
            FROM xp_log
            WHERE class_id=? AND DATE(created_at) >= ?
            GROUP BY user_id, full_name
            ORDER BY total DESC
            LIMIT 3
            """,
            (class_id, since),
        )

    rows = cur.fetchall()
    conn.close()
    return rows


def mark_weekly_run_if_new(class_id: int, week_start: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    try:
        if _is_psycopg_conn(conn):
            cur.execute(
                """
                INSERT INTO weekly_runs (class_id, week_start)
                VALUES (%s, %s)
                ON CONFLICT (class_id, week_start) DO NOTHING
                """,
                (class_id, week_start),
            )
            conn.commit()
            return cur.rowcount == 1
        else:
            cur.execute("INSERT INTO weekly_runs (class_id, week_start) VALUES (?, ?)", (class_id, week_start))
            conn.commit()
            return True
    except Exception:
        return False
    finally:
        conn.close()