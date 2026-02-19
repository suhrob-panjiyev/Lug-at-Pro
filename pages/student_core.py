import streamlit as st
import random
import json
import csv
from pathlib import Path
import requests
import pandas as pd
from typing import Optional, List

APP_TITLE = "Lug'at Pro — Student"
BASE_CSV = Path("5000_lugat_en_uz.csv")
USER_DATA_FILE = Path("user_words.json")
STATS_FILE = Path("stats.json")
QUESTIONS_PER_TEST = 10


# ---------------------------
# Sidebar (Custom Nav)
# ---------------------------
def render_sidebar(active: str = "student"):
    with st.sidebar:
        st.markdown("## 📘 Lug'at Pro")
        st.caption("Student bo‘limi")

        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

        # Active student page highlight (oddiy)
        if st.button("🎓 Student", use_container_width=True, type="primary" if active == "student" else "secondary"):
            st.switch_page("pages/1_Student.py")  # eski link qoladi (breaking bo‘lmasin)

        if st.button("👨‍🏫 Teacher", use_container_width=True):
            st.switch_page("pages/2_Teacher.py")

        if st.button("👤 Sayt haqimda", use_container_width=True):
            st.switch_page("pages/3_About.py")

        st.divider()
        st.caption("© 2026 • Built by Suhrob")


# ---------------------------
# Normalizers
# ---------------------------
def norm_en(s: str) -> str:
    return " ".join(s.strip().lower().split())

def norm_uz(s: str) -> str:
    return " ".join(s.strip().lower().split())


# ---------------------------
# CSV loader (BOM fixed)
# ---------------------------
def _clean_header(h: str) -> str:
    return str(h).replace("\ufeff", "").strip().lower()

def detect_columns(fieldnames):
    if not fieldnames:
        return None, None
    cleaned = [_clean_header(f) for f in fieldnames]

    en_candidates = ["en", "english", "word", "eng"]
    uz_candidates = ["uz", "uzbek", "translation", "meaning", "tr", "uzb"]

    en_col = None
    uz_col = None

    for c in en_candidates:
        if c in cleaned:
            en_col = fieldnames[cleaned.index(c)]
            break
    for c in uz_candidates:
        if c in cleaned:
            uz_col = fieldnames[cleaned.index(c)]
            break

    return en_col, uz_col

@st.cache_data(show_spinner=False)
def load_base_csv(path_str: str):
    path = Path(path_str)
    data = {}
    meta = {"ok": False, "rows": 0, "en_col": None, "uz_col": None, "error": None}

    if not path.exists():
        meta["error"] = f"CSV topilmadi: {path.resolve()}"
        return data, meta

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            en_col, uz_col = detect_columns(reader.fieldnames)

            meta["en_col"] = en_col
            meta["uz_col"] = uz_col

            if not en_col or not uz_col:
                meta["error"] = f"Ustun topilmadi. Fieldnames: {reader.fieldnames}"
                return data, meta

            for row in reader:
                meta["rows"] += 1
                en = (row.get(en_col) or "").strip()
                uz = (row.get(uz_col) or "").strip()
                if not en or not uz:
                    continue
                k = norm_en(en)
                data.setdefault(k, {"en": en, "uz_list": []})
                if all(norm_uz(uz) != norm_uz(x) for x in data[k]["uz_list"]):
                    data[k]["uz_list"].append(uz)

        meta["ok"] = True
        return data, meta

    except Exception as e:
        meta["error"] = str(e)
        return data, meta


# ---------------------------
# User words
# ---------------------------
def load_user_words():
    if not USER_DATA_FILE.exists():
        return {}
    try:
        raw = json.loads(USER_DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return {}
        data = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            en = str(item.get("en", "")).strip()
            uz_list = item.get("uz_list") or []
            uz_list = [str(x).strip() for x in uz_list if str(x).strip()]
            if not en or not uz_list:
                continue
            data[norm_en(en)] = {"en": en, "uz_list": uz_list}
        return data
    except Exception:
        return {}

def save_user_words(user_map: dict):
    arr = [{"en": v["en"], "uz_list": v["uz_list"]} for v in user_map.values()]
    USER_DATA_FILE.write_text(json.dumps(arr, ensure_ascii=False, indent=2), encoding="utf-8")

@st.cache_data(show_spinner=False)
def english_list_from_map(map_: dict):
    return sorted({v["en"] for v in map_.values()}, key=lambda x: x.lower())

def suggestions(query: str, english_list: List[str], limit: int = 16):
    q = norm_en(query)
    if not q:
        return []
    starts = [w for w in english_list if w.lower().startswith(q)]
    if len(starts) >= limit:
        return starts[:limit]
    contains = [w for w in english_list if q in w.lower() and w not in starts]
    return (starts + contains)[:limit]


# ---------------------------
# Translation fallback
# ---------------------------
@st.cache_data(show_spinner=False)
def translate_mymemory(en_text: str):
    en_text = en_text.strip()
    if not en_text:
        return []
    url = "https://api.mymemory.translated.net/get"
    params = {"q": en_text, "langpair": "en|uz"}
    r = requests.get(url, params=params, timeout=12)
    r.raise_for_status()
    data = r.json()

    candidates = []
    main = (data.get("responseData") or {}).get("translatedText", "")
    if main:
        candidates.append(main)

    for m in (data.get("matches") or []):
        t = (m.get("translation") or "").strip()
        if t:
            candidates.append(t)

    cleaned, seen = [], set()
    for c in candidates:
        c2 = " ".join(c.strip().split())
        key = c2.lower()
        if c2 and key not in seen:
            seen.add(key)
            cleaned.append(c2)

    return cleaned[:10]

def is_weird_translation(t: str) -> bool:
    s = t.strip().lower()
    if not s:
        return True
    if len(s) > 35:
        return True
    if any(x in s for x in ["3d", "histogram", "gistogram", "diagram", "grafik"]):
        return True
    if "-" in s and len(s) > 18:
        return True
    return False


# ---------------------------
# Stats persistence
# ---------------------------
def load_stats():
    if not STATS_FILE.exists():
        return {"manual": {"attempts": 0, "total_q": 0, "correct_q": 0}, "csv": {"tests": {}}}
    try:
        obj = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            raise ValueError("bad stats")
        obj.setdefault("manual", {"attempts": 0, "total_q": 0, "correct_q": 0})
        obj.setdefault("csv", {"tests": {}})
        obj["csv"].setdefault("tests", {})
        return obj
    except Exception:
        return {"manual": {"attempts": 0, "total_q": 0, "correct_q": 0}, "csv": {"tests": {}}}

def save_stats(stats_obj: dict):
    STATS_FILE.write_text(json.dumps(stats_obj, ensure_ascii=False, indent=2), encoding="utf-8")

def record_manual_result(stats_obj: dict, correct: int, total: int):
    stats_obj["manual"]["attempts"] = int(stats_obj["manual"].get("attempts", 0)) + 1
    stats_obj["manual"]["total_q"] = int(stats_obj["manual"].get("total_q", 0)) + total
    stats_obj["manual"]["correct_q"] = int(stats_obj["manual"].get("correct_q", 0)) + correct

def record_csv_result(stats_obj: dict, test_id: int, correct: int, total: int):
    t = stats_obj["csv"]["tests"].get(str(test_id), {"attempts": 0, "total_q": 0, "correct_q": 0})
    t["attempts"] = int(t.get("attempts", 0)) + 1
    t["total_q"] = int(t.get("total_q", 0)) + total
    t["correct_q"] = int(t.get("correct_q", 0)) + correct
    stats_obj["csv"]["tests"][str(test_id)] = t

def acc_pct(correct: int, total: int) -> float:
    return (correct / total * 100.0) if total else 0.0


# ---------------------------
# Quiz helpers
# ---------------------------
def unique_all_uz(map_: dict):
    seen = set()
    out = []
    for v in map_.values():
        for u in (v.get("uz_list") or []):
            nu = norm_uz(u)
            if u.strip() and nu not in seen:
                seen.add(nu)
                out.append(u)
    return out

def build_question_from_map(map_: dict, en_key: str):
    item = map_[en_key]
    en = item["en"]
    uz_list = item.get("uz_list") or []
    correct = random.choice(uz_list) if uz_list else "(tarjima yo‘q)"

    pool = unique_all_uz(map_)
    pool = [u for u in pool if norm_uz(u) != norm_uz(correct)]
    random.shuffle(pool)
    wrongs = pool[:3]

    fillers = ["velosiped", "samolyot", "poyezd", "telefon", "kitob", "daraxt", "stol", "qalam"]
    for f in fillers:
        if len(wrongs) >= 3:
            break
        if norm_uz(f) != norm_uz(correct) and all(norm_uz(f) != norm_uz(w) for w in wrongs):
            wrongs.append(f)

    options = [correct] + wrongs[:3]
    random.shuffle(options)
    return {"en": en, "correct": correct, "options": options}

def start_quiz(mode: str, keys: List[str], csv_test_id: Optional[int] = None):
    st.session_state.quiz_mode = mode
    st.session_state.quiz_keys = keys
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answers = []
    st.session_state.quiz_page = "run"
    st.session_state.csv_test_id = csv_test_id
    st.session_state.result_saved = False

def reset_quiz_to_menu():
    st.session_state.quiz_page = "menu"
    st.session_state.quiz_mode = None
    st.session_state.quiz_keys = []
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answers = []
    st.session_state.csv_test_id = None
    st.session_state.current_q = None
    st.session_state.current_q_id = None
    st.session_state.q_choice = None
    st.session_state.pop("q_choice_widget", None)


# ---------------------------
# State
# ---------------------------
def ensure_state():
    if "base_map" not in st.session_state or "csv_meta" not in st.session_state:
        base_map, meta = load_base_csv(str(BASE_CSV))
        st.session_state.base_map = base_map
        st.session_state.csv_meta = meta

    if "user_map" not in st.session_state:
        st.session_state.user_map = load_user_words()

    if "english_list_csv" not in st.session_state:
        st.session_state.english_list_csv = english_list_from_map(st.session_state.base_map)

    if "quiz_page" not in st.session_state:
        st.session_state.quiz_page = "menu"
    if "quiz_mode" not in st.session_state:
        st.session_state.quiz_mode = None
    if "quiz_keys" not in st.session_state:
        st.session_state.quiz_keys = []
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0
    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = []
    if "csv_test_id" not in st.session_state:
        st.session_state.csv_test_id = None

    if "last_translations" not in st.session_state:
        st.session_state.last_translations = []

    if "stats_obj" not in st.session_state:
        st.session_state.stats_obj = load_stats()

    if "current_q" not in st.session_state:
        st.session_state.current_q = None
    if "current_q_id" not in st.session_state:
        st.session_state.current_q_id = None
    if "q_choice" not in st.session_state:
        st.session_state.q_choice = None

    if "student_section" not in st.session_state:
        st.session_state.student_section = "add"
    if "stats_view" not in st.session_state:
        st.session_state.stats_view = "manual"

    if "en_input" not in st.session_state:
        st.session_state.en_input = ""
    if "en_nonce" not in st.session_state:
        st.session_state.en_nonce = 0


# ---------------------------
# Shared UI (CSS + hero + top nav)
# ---------------------------
def inject_student_css():
    st.markdown(
        """
        <style>
          .hero{
            padding: 18px 18px;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.10);
            background: linear-gradient(135deg, rgba(80,120,255,0.20), rgba(0,0,0,0));
          }
          .pill{
            display:inline-block;
            padding:6px 10px;
            border-radius:999px;
            border:1px solid rgba(255,255,255,0.14);
            background: rgba(255,255,255,0.04);
            font-size:13px;
            margin-right:8px;
          }
          .card{
            padding: 14px 14px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.03);
          }
          .qa-card{
            padding: 14px 14px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.03);
            margin-bottom: 10px;
          }
          .muted{opacity:.82}
          .big{font-size:34px;font-weight:800;line-height:1.05}
          .sug-title{margin-top:8px;margin-bottom:6px}
        </style>
        """,
        unsafe_allow_html=True
    )

def render_hero():
    st.markdown(
        """
        <div class="hero">
          <div class="big">🎓 Student</div>
          <div class="muted" style="margin-top:6px">So‘z qo‘shing → test ishlang → natijani ko‘ring.</div>
          <div style="margin-top:10px">
            <span class="pill">✅ Tavsiya</span>
            <span class="pill">✅ 2 xil test</span>
            <span class="pill">✅ Statistika</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

import streamlit as st

def render_top_nav(active: str = "add", page_key: str = "student", **kwargs):
    """
    active: "add" | "test" | "stats"
    page_key: har bir page uchun unik prefix
    """
    k_add = f"{page_key}_nav_add"
    k_test = f"{page_key}_nav_test"
    k_stats = f"{page_key}_nav_stats"

    n1, n2, n3 = st.columns(3)

    with n1:
        if st.button("➕ So‘z qo‘shish", key=k_add, use_container_width=True,
                     type="primary" if active == "add" else "secondary"):
            st.switch_page("pages/1_1_suz_qushish.py")

    with n2:
        if st.button("📝 Test", key=k_test, use_container_width=True,
                     type="primary" if active == "test" else "secondary"):
            st.switch_page("pages/1_2_test.py")

    with n3:
        if st.button("📊 Statistika", key=k_stats, use_container_width=True,
                     type="primary" if active == "stats" else "secondary"):
            st.switch_page("pages/1_3_statistika.py")
