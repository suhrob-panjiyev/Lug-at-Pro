from core.db import get_conn
from core.text import norm_en, norm_uz


def get_user_words_map(user_id: int) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT en, uz FROM words WHERE user_id=? ORDER BY en", (user_id,))
    rows = cur.fetchall()
    conn.close()

    mp = {}
    for r in rows:
        en = r["en"]
        uz = r["uz"]
        k = norm_en(en)
        mp.setdefault(k, {"en": en, "uz_list": []})
        # dedupe norm
        if all(norm_uz(uz) != norm_uz(x) for x in mp[k]["uz_list"]):
            mp[k]["uz_list"].append(uz)
    return mp


def upsert_word(user_id: int, en: str, uz_list: list[str]) -> None:
    """Berilgan en uchun uz_list ni DBda UNIQUE bilan saqlaydi."""
    conn = get_conn()
    cur = conn.cursor()

    en = en.strip()
    for uz in uz_list:
        uz = uz.strip()
        if not en or not uz:
            continue
        cur.execute(
            "INSERT OR IGNORE INTO words (user_id, en, uz) VALUES (?, ?, ?)",
            (user_id, en, uz),
        )

    conn.commit()
    conn.close()