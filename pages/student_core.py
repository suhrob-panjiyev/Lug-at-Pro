import streamlit as st
import requests
from typing import Optional, List
from pathlib import Path

# =========================
# CONFIG + TEXT
# =========================
from core.config import (
    APP_TITLE, BASE_CSV, USER_DATA_FILE, STATS_FILE, QUESTIONS_PER_TEST
)
from core.text import norm_en, norm_uz

# =========================
# REPOS
# =========================
from core.csv_repo import load_base_csv as _load_base_csv
from core.user_repo import (
    load_user_words as _load_user_words,
    save_user_words as _save_user_words,
    english_list_from_map as _english_list_from_map,
)

# =========================
# STATS (new API) + wrappers
# =========================
from core.stats_repo import (
    load_stats as _load_stats,
    save_stats as _save_stats,
    sanitize_stats,
    acc_pct,
    record_manual_result,
    record_csv_result,
    record_level_result,
)

# =========================
# QUIZ (logic)
# =========================
from core.quiz import (
    build_question_from_map as _build_question_from_map,
    start_quiz_state as _start_quiz_state,
    reset_quiz_state as _reset_quiz_state,
)

# =========================
# UI (student)
# =========================
from ui.student_ui import (
    render_sidebar as _render_sidebar,
    inject_student_css as _inject_student_css,
    render_hero as _render_hero,
    render_top_nav as _render_top_nav,
)
from services.translation_service import translate_mymemory, is_weird_translation
from services.suggestion_service import suggestions
# =========================================================
# Backward-compatible wrappers (pages import qiladigan API)
# =========================================================

def render_sidebar(active: str = "student"):
    return _render_sidebar(active=active)

def inject_student_css():
    return _inject_student_css()

def render_hero():
    return _render_hero()

def render_top_nav(active: str = "add", page_key: str = "student", **kwargs):
    return _render_top_nav(active=active, page_key=page_key)

def load_base_csv(path_str: str):
    return _load_base_csv(path_str)

def load_user_words():
    return _load_user_words(USER_DATA_FILE)

def save_user_words(user_map: dict) -> None:
    _save_user_words(USER_DATA_FILE, user_map)

def english_list_from_map(map_: dict):
    return _english_list_from_map(map_)

def build_question_from_map(map_: dict, en_key: str):
    return _build_question_from_map(map_, en_key)

def start_quiz(mode: str, keys: List[str], csv_test_id: Optional[int] = None):
    return _start_quiz_state(st.session_state, mode, keys, csv_test_id=csv_test_id)

def reset_quiz_to_menu():
    return _reset_quiz_state(st.session_state)

def load_stats() -> dict:
    return _load_stats(STATS_FILE)

def save_stats(stats_obj: dict) -> None:
    _save_stats(STATS_FILE, stats_obj)

# =========================================================
# STATE
# =========================================================
def ensure_state():
    # CSV map
    if "base_map" not in st.session_state or "csv_meta" not in st.session_state:
        base_map, meta = load_base_csv(str(BASE_CSV))
        st.session_state.base_map = base_map
        st.session_state.csv_meta = meta

    # User words
    if "user_map" not in st.session_state:
        st.session_state.user_map = load_user_words()

    # english list
    if "english_list_csv" not in st.session_state:
        st.session_state.english_list_csv = english_list_from_map(st.session_state.base_map)

    # quiz state defaults
    st.session_state.setdefault("quiz_page", "menu")
    st.session_state.setdefault("quiz_mode", None)
    st.session_state.setdefault("quiz_keys", [])
    st.session_state.setdefault("quiz_index", 0)
    st.session_state.setdefault("quiz_score", 0)
    st.session_state.setdefault("quiz_answers", [])
    st.session_state.setdefault("csv_test_id", None)
    st.session_state.setdefault("result_saved", False)

    # misc
    st.session_state.setdefault("last_translations", [])
    st.session_state.setdefault("current_q", None)
    st.session_state.setdefault("current_q_id", None)
    st.session_state.setdefault("q_choice", None)

    st.session_state.setdefault("student_section", "add")
    st.session_state.setdefault("stats_view", "manual")

    st.session_state.setdefault("en_input", "")
    st.session_state.setdefault("en_nonce", 0)

    # level test
    st.session_state.setdefault("current_level", "-")

    # stats obj
    if "stats_obj" not in st.session_state:
        st.session_state.stats_obj = sanitize_stats(load_stats())
    else:
        st.session_state.stats_obj = sanitize_stats(st.session_state.stats_obj)

# =========================================================
# GUARD
# =========================================================
def require_login():
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Davom etish uchun avval login qiling 🙂")
        st.switch_page("app.py")
        st.stop()