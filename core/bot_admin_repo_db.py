# core/bot_admin_repo_db.py
import sqlite3  
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import csv, json, random
from pathlib import Path

def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]  # Mini_Lugat/

def _base_csv_path() -> Path:
    return _project_root() / "5000_lugat_en_uz.csv"

def _load_pairs(limit: int = 5000):
    path = _base_csv_path()
    items = []
    if not path.exists():
        return items

    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return items

        # ustunlarni topamiz (en/uz)
        fn = [x.strip().lower().replace("\ufeff", "") for x in reader.fieldnames]
        def pick(cols):
            for c in cols:
                if c in fn:
                    return reader.fieldnames[fn.index(c)]
            return None

        en_col = pick(["en","english","word","eng"])
        uz_col = pick(["uz","uzbek","translation","meaning","tr","uzb"])
        if not en_col or not uz_col:
            return items

        for row in reader:
            en = (row.get(en_col) or "").strip()
            uz = (row.get(uz_col) or "").strip()
            if en and uz:
                items.append((en, uz))
            if len(items) >= limit:
                break
    return items

def _split_uz(uz: str):
    return [p.strip() for p in str(uz).split(",") if p.strip()]

def build_fixed_quiz_web(n: int, seed: int, k_options: int = 4):
    rnd = random.Random(seed)
    pairs = list({(en, uz) for en, uz in _load_pairs(limit=5000)})
    rnd.shuffle(pairs)
    questions = pairs[: max(0, n)]
    all_uz = [uz for _, uz in pairs if uz]

    payload = []
    for en, uz in questions:
        translations = _split_uz(uz)
        correct = rnd.choice(translations) if translations else uz.strip()
        synonyms = set(translations)
        wrong = list({u for u in all_uz if u and (u not in synonyms) and (u != correct)})
        rnd.shuffle(wrong)
        opts = [correct] + wrong[: max(0, k_options - 1)]
        rnd.shuffle(opts)
        payload.append({"en": en, "uz": uz, "options": opts})
    return payload

def ensure_announcements_table(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        assignment_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',  -- pending/sent/error
        error TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        sent_at TEXT
    )
    """)

def _bot_db_path() -> Path:
    # core/ ichidan 1 tepaga -> Mini_Lugat/
    root = Path(__file__).resolve().parents[1]
    return root / "data" / "classroom.db"


def get_bot_conn() -> sqlite3.Connection:
    db_path = _bot_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def bot_kpis() -> dict:
    conn = get_bot_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS n FROM classes")
    classes_n = cur.fetchone()["n"]

    cur.execute("SELECT COUNT(DISTINCT user_id) AS n FROM members")
    students_n = cur.fetchone()["n"]

    cur.execute("SELECT COUNT(*) AS n FROM assignments")
    assignments_n = cur.fetchone()["n"]

    cur.execute("SELECT COUNT(*) AS n FROM attempts")
    attempts_n = cur.fetchone()["n"]

    cur.execute("SELECT AVG(pct) AS v FROM attempts")
    avg_pct = cur.fetchone()["v"] or 0.0

    conn.close()
    return {
        "classes": int(classes_n),
        "students": int(students_n),
        "assignments": int(assignments_n),
        "attempts": int(attempts_n),
        "avg_pct": float(avg_pct),
    }


def list_classes() -> pd.DataFrame:
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
    conn = get_bot_conn()
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def list_assignments(class_id: int) -> pd.DataFrame:
    q = """
    SELECT
        a.id,
        a.class_id,
        a.n_questions,
        a.deadline_hhmm,
        a.deadline_at,
        a.is_active,
        a.created_at,
        (SELECT COUNT(*) FROM attempts t WHERE t.assignment_id = a.id) AS attempts_count,
        (SELECT AVG(pct) FROM attempts t WHERE t.assignment_id = a.id) AS avg_pct
    FROM assignments a
    WHERE a.class_id = ?
    ORDER BY a.id DESC
    """
    conn = get_bot_conn()
    df = pd.read_sql_query(q, conn, params=(class_id,))
    conn.close()
    return df


def list_attempts(assignment_id: int) -> pd.DataFrame:
    q = """
    SELECT
        id,
        user_id,
        full_name,
        score,
        total,
        pct,
        finished_at,
        COALESCE(is_late, 0) AS is_late
    FROM attempts
    WHERE assignment_id = ?
    ORDER BY pct DESC, finished_at DESC
    """
    conn = get_bot_conn()
    df = pd.read_sql_query(q, conn, params=(assignment_id,))
    conn.close()
    return df


def daily_top(class_id: int, limit: int = 10) -> pd.DataFrame:
    q = """
    SELECT
        user_id,
        full_name,
        SUM(xp) AS xp
    FROM xp_log
    WHERE class_id = ?
      AND date(created_at) = date('now','localtime')
    GROUP BY user_id, full_name
    ORDER BY xp DESC
    LIMIT ?
    """
    conn = get_bot_conn()
    df = pd.read_sql_query(q, conn, params=(class_id, limit))
    conn.close()
    return df


def weekly_top(class_id: int, limit: int = 10) -> pd.DataFrame:
    # haftani dushanbadan boshlab hisoblaymiz (SQLite trick)
    q = """
    SELECT
        user_id,
        full_name,
        SUM(xp) AS xp
    FROM xp_log
    WHERE class_id = ?
      AND date(created_at) >= date('now','weekday 1','-7 days','localtime')
    GROUP BY user_id, full_name
    ORDER BY xp DESC
    LIMIT ?
    """
    conn = get_bot_conn()
    df = pd.read_sql_query(q, conn, params=(class_id, limit))
    conn.close()
    return df



TZ = ZoneInfo("Asia/Samarkand")


def _deadline_at_for_today(deadline_hhmm: str | None) -> str | None:
    """HH:MM -> bugungi sana bilan ISO datetime (Asia/Samarkand)."""
    if not deadline_hhmm:
        return None
    s = deadline_hhmm.strip()
    if len(s) != 5 or s[2] != ":":
        return None
    try:
        hh = int(s[:2]); mm = int(s[3:])
    except Exception:
        return None
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None

    now = datetime.now(TZ)
    dl = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return dl.isoformat()


def create_assignment_web(class_id: int, n_questions: int, deadline_hhmm: str | None, deactivate_prev: bool = True) -> int:
    """
    Web(Admin)dan assignment yaratish:
    - ixtiyoriy: oldingilarni is_active=0 qilish
    - deadline_hhmm saqlash
    - deadline_at ham to‘ldirish (bot logikasiga mos)
    """
    dl_at = _deadline_at_for_today(deadline_hhmm)

    conn = get_bot_conn()
    cur = conn.cursor()
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
    ensure_announcements_table(cur)

    try:
        if deactivate_prev:
            cur.execute("UPDATE assignments SET is_active=0 WHERE class_id=?", (class_id,))

        cur.execute(
            "INSERT INTO assignments (class_id, n_questions, deadline_hhmm, deadline_at, is_active) VALUES (?, ?, ?, ?, 1)",
            (class_id, int(n_questions), deadline_hhmm, dl_at),
        )
        aid = int(cur.lastrowid)
        # ✅ testni tayyorlab DBga yozamiz (xuddi /give_hw kabi)
        fixed = build_fixed_quiz_web(int(n_questions), seed=aid, k_options=4)
        cur.execute("UPDATE assignments SET questions_json=? WHERE id=?", (json.dumps(fixed, ensure_ascii=False), aid))

        # ✅ announce queue (bot keyin guruhga yuboradi)
        cur.execute(
            "INSERT INTO announcements (class_id, assignment_id, status) VALUES (?, ?, 'pending')",
            (class_id, aid),
        )

        conn.commit()
        return aid
    finally:
        conn.close()


def set_assignment_active(assignment_id: int, class_id: int, active: bool) -> None:
    """Tanlangan assignmentni active/deactive qilish. Active qilinsa boshqalarni o‘chiradi."""
    conn = get_bot_conn()
    cur = conn.cursor()
    try:
        if active:
            cur.execute("UPDATE assignments SET is_active=0 WHERE class_id=?", (class_id,))
            cur.execute("UPDATE assignments SET is_active=1 WHERE id=?", (assignment_id,))
        else:
            cur.execute("UPDATE assignments SET is_active=0 WHERE id=?", (assignment_id,))
        conn.commit()
    finally:
        conn.close()