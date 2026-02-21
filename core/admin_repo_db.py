from core.db import get_conn


def list_users_with_metrics(q: str = "", sort: str = "last_login_desc") -> list[dict]:
    q = (q or "").strip().lower()

    conn = get_conn()
    cur = conn.cursor()

    # NOTE: attempts va words join qilib aggregate qilamiz
    sql = """
    SELECT
        u.id,
        u.phone,
        u.first_name,
        u.last_name,
        u.created_at,
        u.last_login_at,

        (SELECT COUNT(*) FROM words w WHERE w.user_id = u.id) AS words_count,

        (SELECT COUNT(*) FROM attempts a WHERE a.user_id = u.id) AS attempts_count,

        (SELECT COALESCE(AVG(a.pct), 0) FROM attempts a WHERE a.user_id = u.id) AS avg_pct
    FROM users u
    """

    rows = [dict(r) for r in cur.execute(sql).fetchall()]
    conn.close()

    # filter
    if q:
        rows = [
            r for r in rows
            if q in (r["phone"] or "").lower()
            or q in (r["first_name"] or "").lower()
            or q in (r["last_name"] or "").lower()
        ]

    # sort
    if sort == "last_login_desc":
        rows.sort(key=lambda x: (x["last_login_at"] or ""), reverse=True)
    elif sort == "avg_pct_desc":
        rows.sort(key=lambda x: float(x["avg_pct"] or 0), reverse=True)
    elif sort == "attempts_desc":
        rows.sort(key=lambda x: int(x["attempts_count"] or 0), reverse=True)
    elif sort == "words_desc":
        rows.sort(key=lambda x: int(x["words_count"] or 0), reverse=True)

    return rows


def get_user_attempts(user_id: int, limit: int = 100) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute(
        """
        SELECT id, mode, test_id, level, score, total, pct, ts
        FROM attempts
        WHERE user_id=?
        ORDER BY ts DESC
        LIMIT ?
        """,
        (int(user_id), int(limit)),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_attempts_summary(user_id: int) -> dict:
    conn = get_conn()
    cur = conn.cursor()

    # overall
    overall = cur.execute(
        """
        SELECT
            COUNT(*) attempts,
            COALESCE(SUM(total),0) total_q,
            COALESCE(SUM(score),0) correct_q,
            COALESCE(AVG(pct),0) avg_pct
        FROM attempts
        WHERE user_id=?
        """,
        (int(user_id),),
    ).fetchone()

    # by mode
    by_mode_rows = cur.execute(
        """
        SELECT mode,
               COUNT(*) attempts,
               COALESCE(SUM(total),0) total_q,
               COALESCE(SUM(score),0) correct_q,
               COALESCE(AVG(pct),0) avg_pct
        FROM attempts
        WHERE user_id=?
        GROUP BY mode
        """,
        (int(user_id),),
    ).fetchall()

    conn.close()

    by_mode = {r["mode"]: dict(r) for r in by_mode_rows}
    return {"overall": dict(overall), "by_mode": by_mode}