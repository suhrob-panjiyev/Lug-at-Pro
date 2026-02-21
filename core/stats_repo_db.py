from datetime import datetime
from core.db import get_conn


def add_attempt(user_id: int, mode: str, score: int, total: int, test_id: int | None = None, level: str | None = None) -> None:
    pct = (score / total * 100.0) if total else 0.0
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO attempts (user_id, mode, test_id, level, score, total, pct, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, mode, test_id, level, int(score), int(total), float(pct), ts),
    )
    conn.commit()
    conn.close()


def get_stats_obj(user_id: int) -> dict:
    conn = get_conn()
    cur = conn.cursor()

    # ---------- MANUAL ----------
    cur.execute(
        "SELECT COUNT(*) a, COALESCE(SUM(total),0) t, COALESCE(SUM(score),0) c FROM attempts WHERE user_id=? AND mode='manual'",
        (user_id,),
    )
    m = cur.fetchone()
    manual = {"attempts": int(m["a"]), "total_q": int(m["t"]), "correct_q": int(m["c"]), "history": []}

    cur.execute(
        "SELECT ts, score, total, pct FROM attempts WHERE user_id=? AND mode='manual' ORDER BY ts",
        (user_id,),
    )
    manual["history"] = [{"ts": r["ts"], "correct": int(r["score"]), "total": int(r["total"]), "pct": float(r["pct"])} for r in cur.fetchall()]

    # ---------- CSV (tests aggregate) ----------
    cur.execute(
        """
        SELECT test_id,
               COUNT(*) attempts,
               COALESCE(SUM(total),0) total_q,
               COALESCE(SUM(score),0) correct_q
        FROM attempts
        WHERE user_id=? AND mode='csv' AND test_id IS NOT NULL
        GROUP BY test_id
        """,
        (user_id,),
    )
    tests = {}
    for r in cur.fetchall():
        tid = int(r["test_id"])
        tests[str(tid)] = {"attempts": int(r["attempts"]), "total_q": int(r["total_q"]), "correct_q": int(r["correct_q"])}

    cur.execute(
        "SELECT ts, test_id, score, total, pct FROM attempts WHERE user_id=? AND mode='csv' AND test_id IS NOT NULL ORDER BY ts",
        (user_id,),
    )
    csv_hist = [{"ts": r["ts"], "test_id": int(r["test_id"]), "correct": int(r["score"]), "total": int(r["total"]), "pct": float(r["pct"])} for r in cur.fetchall()]

    csv = {"tests": tests, "history": csv_hist}

    # ---------- LEVEL ----------
    cur.execute(
        """
        SELECT level,
               COUNT(*) attempts,
               COALESCE(SUM(total),0) total_q,
               COALESCE(SUM(score),0) correct_q
        FROM attempts
        WHERE user_id=? AND mode='level' AND level IS NOT NULL
        GROUP BY level
        """,
        (user_id,),
    )
    by_level = {}
    for r in cur.fetchall():
        lv = str(r["level"]).upper()
        by_level[lv] = {"attempts": int(r["attempts"]), "total_q": int(r["total_q"]), "correct_q": int(r["correct_q"])}

    cur.execute(
        "SELECT ts, level, score, total, pct FROM attempts WHERE user_id=? AND mode='level' AND level IS NOT NULL ORDER BY ts",
        (user_id,),
    )
    lvl_hist = [{"ts": r["ts"], "level": str(r["level"]).upper(), "correct": int(r["score"]), "total": int(r["total"]), "pct": float(r["pct"])} for r in cur.fetchall()]

    level = {"by_level": by_level, "history": lvl_hist}

    conn.close()
    return {"manual": manual, "csv": csv, "level": level}