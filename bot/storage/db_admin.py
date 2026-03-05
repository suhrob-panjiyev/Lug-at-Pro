# bot/storage/db_admin.py
from __future__ import annotations
import json
from typing import Any

from bot.storage.db import get_conn, _is_postgres

def _fetchall_dict(cur) -> list[dict]:
    rows = cur.fetchall()
    # psycopg cursor -> tuple bo'lishi mumkin, sqlite -> Row
    out = []
    for r in rows:
        try:
            out.append(dict(r))
        except Exception:
            # tuple fallback: cursor.description dan keylar olamiz
            cols = [d[0] for d in cur.description]
            out.append({cols[i]: r[i] for i in range(len(cols))})
    return out

def bot_kpis() -> dict:
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS n FROM classes")
        classes_n = cur.fetchone()[0] if not hasattr(cur.fetchone(), "__getitem__") else cur.fetchone()["n"]

        # sqlite Row bilan 2 marta fetch bo'lib ketmasin:
        cur.execute("SELECT COUNT(*) AS n FROM classes")
        row = cur.fetchone()
        classes_n = row["n"] if hasattr(row, "keys") else row[0]

        cur.execute("SELECT COUNT(DISTINCT user_id) AS n FROM members")
        row = cur.fetchone()
        students_n = row["n"] if hasattr(row, "keys") else row[0]

        cur.execute("SELECT COUNT(*) AS n FROM assignments")
        row = cur.fetchone()
        assignments_n = row["n"] if hasattr(row, "keys") else row[0]

        cur.execute("SELECT COUNT(*) AS n FROM attempts")
        row = cur.fetchone()
        attempts_n = row["n"] if hasattr(row, "keys") else row[0]

        cur.execute("SELECT AVG(pct) AS v FROM attempts")
        row = cur.fetchone()
        avg_pct = (row["v"] if hasattr(row, "keys") else row[0]) or 0.0

        return {
            "classes": int(classes_n or 0),
            "students": int(students_n or 0),
            "assignments": int(assignments_n or 0),
            "attempts": int(attempts_n or 0),
            "avg_pct": float(avg_pct or 0.0),
        }
    except Exception:
        return {"classes": 0, "students": 0, "assignments": 0, "attempts": 0, "avg_pct": 0.0}
    finally:
        conn.close()

def list_classes() -> list[dict]:
    q = """
    SELECT
        c.id,
        c.name,
        c.group_id,
        c.teacher_id,
        c.created_at,
        (SELECT COUNT(*) FROM members m WHERE m.class_id = c.id) AS members_count,
        (SELECT COUNT(*) FROM assignments a WHERE a.class_id = c.id) AS assignments_count,
        (SELECT COUNT(*) FROM attempts t WHERE t.class_id = c.id) AS attempts_count,
        (SELECT COALESCE(SUM(xp),0) FROM xp_log x WHERE x.class_id = c.id) AS xp_sum
    FROM classes c
    ORDER BY c.id DESC
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(q)
        return _fetchall_dict(cur)
    finally:
        conn.close()

def create_assignment_web(class_id: int, n_questions: int, deadline_hhmm: str | None, deactivate_prev: bool = True) -> int:
    conn = get_conn()
    try:
        cur = conn.cursor()

        # oldingilarni o‘chirish
        if deactivate_prev:
            cur.execute("UPDATE assignments SET is_active=0 WHERE class_id=%s" if _is_postgres() else "UPDATE assignments SET is_active=0 WHERE class_id=?",
                        (int(class_id),))

        # sqlite schema’da deadline_at yo‘q (sizning db.py da sqlite uchun yo‘q)
        # shuning uchun faqat mavjud ustunlar bilan insert qilamiz
        if _is_postgres():
            cur.execute(
                """
                INSERT INTO assignments (class_id, n_questions, deadline_hhmm, is_active)
                VALUES (%s, %s, %s, 1)
                RETURNING id
                """,
                (int(class_id), int(n_questions), deadline_hhmm),
            )
            aid = int(cur.fetchone()[0])
        else:
            cur.execute(
                """
                INSERT INTO assignments (class_id, n_questions, deadline_hhmm, is_active)
                VALUES (?, ?, ?, 1)
                """,
                (int(class_id), int(n_questions), deadline_hhmm),
            )
            aid = int(cur.lastrowid)

        # Savollar JSON — sizda web tarafda build_fixed_quiz_web bo'lsa o'shani import qiling,
        # hozircha placeholder (keyin chiroyli qilamiz)
        fixed = {"n_questions": int(n_questions), "seed": aid, "questions": []}
        cur.execute(
            "UPDATE assignments SET questions_json=%s WHERE id=%s" if _is_postgres() else "UPDATE assignments SET questions_json=? WHERE id=?",
            (json.dumps(fixed, ensure_ascii=False), aid),
        )

        # announcements jadvali bor sizda — queuega qo'shamiz
        cur.execute(
            "INSERT INTO announcements (class_id, assignment_id, status) VALUES (%s, %s, 'pending')" if _is_postgres()
            else "INSERT INTO announcements (class_id, assignment_id, status) VALUES (?, ?, 'pending')",
            (int(class_id), aid),
        )

        conn.commit()
        return aid
    finally:
        conn.close()