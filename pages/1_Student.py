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
def render_sidebar():
    with st.sidebar:
        st.markdown("## 📘 Lug'at Pro")
        st.caption("Student bo‘limi")

        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")

        if st.button("🎓 Student", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Student.py")

        if st.button("👨‍🏫 Teacher", use_container_width=True):
            st.switch_page("pages/2_Teacher.py")

        if st.button("👤 Men haqimda", use_container_width=True):
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
    """
    Kuchli tavsiya:
    - startswith avval
    - keyin contains
    - query 1ta harf bo‘lsa ham ishlaydi
    """
    q = norm_en(query)
    if not q:
        return []
    starts = [w for w in english_list if w.lower().startswith(q)]
    if len(starts) >= limit:
        return starts[:limit]
    contains = [w for w in english_list if q in w.lower() and w not in starts]
    return (starts + contains)[:limit]


# ---------------------------
# Translation fallback (1-best by default)
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

    # dedupe
    cleaned, seen = [], set()
    for c in candidates:
        c2 = " ".join(c.strip().split())
        key = c2.lower()
        if c2 and key not in seen:
            seen.add(key)
            cleaned.append(c2)

    return cleaned[:10]


def is_weird_translation(t: str) -> bool:
    """
    Foydasiz/galati tarjimalarni filter qilish (3D-..., uzun/texnik).
    MVP uchun oddiy heuristika.
    """
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
        st.session_state.quiz_page = "menu"  # menu | csv_list | run | result
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

    # Section nav (tabs o‘rniga)
    if "student_section" not in st.session_state:
        st.session_state.student_section = "add"  # add | test | stats

    # Stats view
    if "stats_view" not in st.session_state:
        st.session_state.stats_view = "manual"  # manual | csv

    # Add page input
    if "en_input" not in st.session_state:
        st.session_state.en_input = ""


# ---------------------------
# UI
# ---------------------------
st.set_page_config(page_title="Student — Lug'at Pro", page_icon="🎓", layout="wide")
render_sidebar()
ensure_state()

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
      .chip{
        display:inline-block;
        padding:6px 10px;
        border-radius:999px;
        border:1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.04);
        font-size:13px;
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

# ---------------------------
# TOP NAV (3 tugma)
# ---------------------------
n1, n2, n3 = st.columns(3)
with n1:
    if st.button("➕ So‘z qo‘shish", use_container_width=True,
                 type="primary" if st.session_state.student_section == "add" else "secondary"):
        st.session_state.student_section = "add"
        st.rerun()
with n2:
    if st.button("📝 Test", use_container_width=True,
                 type="primary" if st.session_state.student_section == "test" else "secondary"):
        st.session_state.student_section = "test"
        st.rerun()
with n3:
    if st.button("📊 Statistika", use_container_width=True,
                 type="primary" if st.session_state.student_section == "stats" else "secondary"):
        st.session_state.student_section = "stats"
        st.rerun()

st.write("")


# =============================================================================
# SECTION: ADD (So‘z qo‘shish)
# =============================================================================
if st.session_state.student_section == "add":
    st.markdown("### ➕ So‘z qo‘shish")

    # --- state ---
    if "en_input" not in st.session_state:
        st.session_state.en_input = ""
    if "en_nonce" not in st.session_state:
        st.session_state.en_nonce = 0  # widget key'ni yangilash uchun

    # --- Text input (dynamic key) ---
    typed = st.text_input(
        "English so‘zni yozing",
        key=f"en_input_widget_{st.session_state.en_nonce}",
        value=st.session_state.en_input,
        placeholder="car, example, apple ..."
    )

    # yozganini state'ga yozamiz
    if typed != st.session_state.en_input:
        st.session_state.en_input = typed

    en_word = (st.session_state.en_input or "").strip()
    en_key = norm_en(en_word)

    # Tavsiyalar
    sug = suggestions(en_word, st.session_state.english_list_csv, limit=16)

    # ✅ Dropdown tavsiya
    if en_word and sug:
        pick = st.selectbox(
            "Tavsiya tanlang (ixtiyoriy):",
            options=["—"] + sug,
            index=0,
            help="Yozishni boshlang → tavsiyalar chiqadi → bittasini tanlang."
        )
        if pick != "—":
            st.session_state.en_input = pick
            st.session_state.en_nonce += 1  # ✅ widget key o‘zgaradi
            st.rerun()

    # ✅ Chip buttonlar
    if en_word:
        st.markdown("<div class='sug-title'><b>Tavsiyalar:</b></div>", unsafe_allow_html=True)

        if not sug:
            st.caption("Hech narsa topilmadi. Yozuvni tekshiring.")
        else:
            cols = st.columns(8)
            for i, w in enumerate(sug):
                with cols[i % 8]:
                    if st.button(w, key=f"sug_{w}_{i}", use_container_width=True):
                        st.session_state.en_input = w
                        st.session_state.en_nonce += 1  # ✅ widget key o‘zgaradi
                        st.rerun()

    st.divider()

    # ---------------------------
    # CSV’da bor bo‘lsa
    # ---------------------------
    if en_key and en_key in st.session_state.base_map:
        item = st.session_state.base_map[en_key]
        st.success("Topildi ✅ (CSV bazadan)")

        existing = item.get("uz_list") or []
        selected = st.multiselect(
            "Tarjimalarni tanlang:",
            existing,
            default=existing[:1] if existing else []
        )

        if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(len(selected) == 0)):
            st.session_state.user_map[en_key] = {"en": item["en"], "uz_list": selected}
            save_user_words(st.session_state.user_map)
            st.success("Saqlandi ✅")

    # ---------------------------
    # CSV’da yo‘q bo‘lsa
    # ---------------------------
    else:
        st.info("Bu so‘z CSV bazada yo‘q. Istasangiz avtomatik tarjima qilib saqlaysiz.")

        a, b, c = st.columns([1.2, 1.2, 1.2])
        with a:
            do_translate = st.button("🔄 Avto tarjima", use_container_width=True, disabled=not en_word)
        with b:
            only_best = st.toggle("⭐ Faqat 1 ta tarjima", value=True)
        with c:
            manual = st.toggle("✍️ Qo‘lda kiritaman", value=False)

        if do_translate and en_word:
            with st.spinner("Tarjima qilinyapti..."):
                try:
                    tr = translate_mymemory(en_word)
                    tr = [x for x in tr if not is_weird_translation(x)]
                    if only_best and tr:
                        tr = tr[:1]
                    st.session_state.last_translations = tr
                except Exception as e:
                    st.session_state.last_translations = []
                    st.error(f"Tarjima xatosi: {e}")

        if manual:
            uz_text = st.text_area("Tarjima (har qatorda bittadan)", placeholder="misol")
            selected = [x.strip() for x in uz_text.splitlines() if x.strip()]
        else:
            default_pick = st.session_state.last_translations[:1] if st.session_state.last_translations else []
            selected = st.multiselect(
                "Topilgan tarjima(lar):",
                st.session_state.last_translations,
                default=default_pick
            )

        if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(not en_word or len(selected) == 0)):
            st.session_state.user_map[en_key] = {"en": en_word, "uz_list": selected}
            save_user_words(st.session_state.user_map)
            st.success("Saqlandi ✅")

    st.write("")
    k1, k2 = st.columns(2)
    k1.metric("User so‘zlari", len(st.session_state.user_map))
    k2.metric("CSV so‘zlari", len(st.session_state.base_map))




# =============================================================================
# SECTION: TEST
# =============================================================================
elif st.session_state.student_section == "test":
    st.markdown("### 📝 Test")

    if st.session_state.quiz_page == "menu":
        c1, c2 = st.columns(2)

        with c1:
            st.markdown(
                "<div class='card'><b>🧑‍💻 Mening so‘zlarim</b><div class='muted'>Siz saqlagan so‘zlardan test.</div></div>",
                unsafe_allow_html=True
            )
            if st.button("Boshlash ▶️", type="primary", use_container_width=True):
                if len(st.session_state.user_map) < 2:
                    st.error("Avval kamida 2 ta so‘z saqlang.")
                else:
                    keys = list(st.session_state.user_map.keys())
                    random.shuffle(keys)
                    keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                    start_quiz("manual", keys)
                    st.rerun()

        with c2:
            st.markdown(
                "<div class='card'><b>📚 CSV testlar</b><div class='muted'>Bazadan bo‘lingan testlar.</div></div>",
                unsafe_allow_html=True
            )
            if st.button("Testlar ro‘yxati ➜", type="primary", use_container_width=True):
                if len(st.session_state.base_map) < QUESTIONS_PER_TEST:
                    st.error("CSV’da yetarli so‘z yo‘q.")
                else:
                    st.session_state.quiz_page = "csv_list"
                    st.rerun()

        st.caption("Har bir test: 10 ta savol.")

    elif st.session_state.quiz_page == "csv_list":
        # ✅ bu yerda siz aytgandek: orqaga + manualga o‘tish tugmalari
        topA, topB, topC = st.columns([1.2, 1.2, 2.0])
        with topA:
            if st.button("⬅️ Test menyu", use_container_width=True):
                reset_quiz_to_menu()
                st.rerun()
        with topB:
            if st.button("🧑‍💻 Mening so‘zlarim testi", use_container_width=True, type="primary"):
                if len(st.session_state.user_map) < 2:
                    st.error("Avval kamida 2 ta so‘z saqlang.")
                else:
                    keys = list(st.session_state.user_map.keys())
                    random.shuffle(keys)
                    keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                    start_quiz("manual", keys)
                    st.rerun()
        with topC:
            q_test = st.text_input("🔎 Test raqami (masalan: 12)", value="", placeholder="...")

        csv_keys_sorted = sorted(st.session_state.base_map.keys())
        total_tests = (len(csv_keys_sorted) + QUESTIONS_PER_TEST - 1) // QUESTIONS_PER_TEST
        tests_stats = st.session_state.stats_obj["csv"]["tests"]

        show_ids = list(range(1, total_tests + 1))
        if q_test.strip().isdigit():
            t = int(q_test.strip())
            show_ids = [t] if 1 <= t <= total_tests else []

        st.write("")
        for t_id in show_ids:
            stat = tests_stats.get(str(t_id))
            if stat and stat.get("total_q", 0) > 0:
                c = int(stat.get("correct_q", 0))
                tot = int(stat.get("total_q", 0))
                w = tot - c
                p = acc_pct(c, tot)
                label = f"Test-{t_id} • ✅ {c} • ❌ {w} • {p:.0f}%"
            else:
                label = f"Test-{t_id} • (hali ishlanmagan)"

            rowA, rowB = st.columns([3, 1])
            with rowA:
                st.write(label)
            with rowB:
                if st.button("▶️", key=f"start_test_{t_id}", use_container_width=True):
                    start_idx = (t_id - 1) * QUESTIONS_PER_TEST
                    chunk = csv_keys_sorted[start_idx:start_idx + QUESTIONS_PER_TEST]
                    start_quiz("csv", chunk, csv_test_id=t_id)
                    st.rerun()

    elif st.session_state.quiz_page == "run":
        mode = st.session_state.quiz_mode
        source_map = st.session_state.user_map if mode == "manual" else st.session_state.base_map
        keys = st.session_state.quiz_keys
        idx = st.session_state.quiz_index
        total_q = len(keys)

        if idx >= total_q:
            st.session_state.quiz_page = "result"
            st.rerun()

        q_id = f"{mode}:{st.session_state.get('csv_test_id')}:{idx}"

        if st.session_state.current_q_id != q_id or st.session_state.current_q is None:
            st.session_state.current_q_id = q_id
            current_key = keys[idx]
            st.session_state.current_q = build_question_from_map(source_map, current_key)
            st.session_state.q_choice = None

        q = st.session_state.current_q
        st.info(("🧑‍💻 Mening so‘zlarim" if mode == "manual" else f"📚 CSV Test-{st.session_state.csv_test_id}") + f" • {idx+1}/{total_q}")

        st.markdown(f"## **{q['en']}**")

        st.session_state.q_choice = st.radio("Tarjimani tanlang:", q["options"], index=None, key="q_choice_widget")
        choice = st.session_state.q_choice

        a, b, c = st.columns([1.2, 1, 1.2])
        with a:
            if st.button("✅ Yuborish", type="primary", use_container_width=True, disabled=(choice is None)):
                ok = (norm_uz(choice) == norm_uz(q["correct"]))
                if ok:
                    st.session_state.quiz_score += 1
                    st.success("To‘g‘ri ✅")
                else:
                    st.error(f"Noto‘g‘ri ❌  To‘g‘risi: **{q['correct']}**")

                st.session_state.quiz_answers.append({"en": q["en"], "your": choice, "correct": q["correct"], "ok": ok})
                st.session_state.quiz_index += 1

                st.session_state.current_q = None
                st.session_state.current_q_id = None
                st.session_state.q_choice = None
                st.session_state.pop("q_choice_widget", None)

                if st.session_state.quiz_index >= total_q:
                    st.session_state.quiz_page = "result"
                st.rerun()

        with b:
            st.metric("Score", f"{st.session_state.quiz_score}/{total_q}")

        with c:
            if st.button("🛑 To‘xtatish", use_container_width=True):
                reset_quiz_to_menu()
                st.rerun()

        st.progress(idx / total_q)

    elif st.session_state.quiz_page == "result":
        mode = st.session_state.quiz_mode
        total_q = len(st.session_state.quiz_keys)
        score = st.session_state.quiz_score
        wrong = total_q - score
        p = acc_pct(score, total_q)

        if "result_saved" not in st.session_state:
            st.session_state.result_saved = False

        if not st.session_state.result_saved:
            if mode == "manual":
                record_manual_result(st.session_state.stats_obj, score, total_q)
            else:
                record_csv_result(st.session_state.stats_obj, st.session_state.csv_test_id, score, total_q)
            save_stats(st.session_state.stats_obj)
            st.session_state.result_saved = True

        mode_title = "🧑‍💻 Mening so‘zlarim" if mode == "manual" else f"📚 CSV Test-{st.session_state.csv_test_id}"

        if p >= 90:
            label = "🔥 A’lo!"
        elif p >= 75:
            label = "✅ Juda yaxshi!"
        elif p >= 50:
            label = "🙂 Yaxshi"
        else:
            label = "💪 Qayta urinib ko‘ring"

        st.markdown(
            f"""
            <div class="hero">
              <div class="pill">{mode_title}</div>
              <div class="pill">Savollar: <b>{total_q}</b></div>
              <div class="pill">To‘g‘ri: <b>{score}</b></div>
              <div class="pill">Noto‘g‘ri: <b>{wrong}</b></div>
              <div style="margin-top:10px" class="big">Natija: {score}/{total_q} • {p:.1f}%</div>
              <div class="muted" style="margin-top:6px">{label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        st.progress(min(max(p / 100.0, 0.0), 1.0))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", f"{score}/{total_q}")
        c2.metric("Aniqlik", f"{p:.1f}%")
        c3.metric("To‘g‘ri", score)
        c4.metric("Noto‘g‘ri", wrong)

        st.divider()

        answers = st.session_state.quiz_answers or []
        if answers:
            df = pd.DataFrame(answers)
            df["status"] = df["ok"].apply(lambda x: "✅" if x else "❌")
            df["en_show"] = df["en"].astype(str)
            df["your_show"] = df["your"].astype(str)
            df["correct_show"] = df["correct"].astype(str)

            f1, f2, f3 = st.columns([1.1, 1.1, 1.6])
            with f1:
                only_wrong = st.toggle("❌ Faqat xatolar", value=(wrong > 0))
            with f2:
                show_table = st.toggle("📊 Jadval", value=False)
            with f3:
                q = st.text_input("🔎 Qidirish", value="", placeholder="car / mashina ...")

            dff = df.copy()
            if only_wrong:
                dff = dff[dff["ok"] == False]

            if q.strip():
                qq = q.strip().lower()
                dff = dff[
                    dff["en_show"].str.lower().str.contains(qq)
                    | dff["your_show"].str.lower().str.contains(qq)
                    | dff["correct_show"].str.lower().str.contains(qq)
                ]

            csv_bytes = dff[["en_show", "your_show", "correct_show", "status"]].rename(
                columns={"en_show": "English", "your_show": "Siz tanlagan", "correct_show": "To‘g‘ri javob", "status": "Holat"}
            ).to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                "⬇️ Natijani CSV qilib olish",
                data=csv_bytes,
                file_name="lugat_test_natija.csv",
                mime="text/csv",
                use_container_width=True
            )

            st.write("")
            if show_table:
                st.dataframe(
                    dff[["status", "en_show", "your_show", "correct_show"]].rename(
                        columns={"status": "", "en_show": "English", "your_show": "Siz tanlagan", "correct_show": "To‘g‘ri javob"}
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                for _, r in dff.iterrows():
                    ok = bool(r["ok"])
                    icon = "✅" if ok else "❌"
                    hint = ""
                    if not ok:
                        hint = f"<div class='muted'>To‘g‘risi: <b>{r['correct_show']}</b></div>"

                    st.markdown(
                        f"""
                        <div class="qa-card">
                          <div style="display:flex; gap:10px; align-items:center;">
                            <div style="font-size:20px">{icon}</div>
                            <div>
                              <div><b>English:</b> {r["en_show"]}</div>
                              <div class="muted"><b>Siz tanlagan:</b> {r["your_show"]}</div>
                              {hint}
                            </div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.divider()
        a, b, c = st.columns(3)
        with a:
            if st.button("⬅️ Menyu", type="primary", use_container_width=True):
                st.session_state.result_saved = False
                reset_quiz_to_menu()
                st.rerun()
        with b:
            if st.button("🔁 Qayta", use_container_width=True):
                st.session_state.result_saved = False
                if mode == "manual":
                    if len(st.session_state.user_map) < 2:
                        st.error("User so‘zlari kam.")
                    else:
                        keys = list(st.session_state.user_map.keys())
                        random.shuffle(keys)
                        keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                        start_quiz("manual", keys)
                        st.rerun()
                else:
                    csv_keys_sorted = sorted(st.session_state.base_map.keys())
                    t_id = st.session_state.csv_test_id
                    start_idx = (t_id - 1) * QUESTIONS_PER_TEST
                    chunk = csv_keys_sorted[start_idx:start_idx + QUESTIONS_PER_TEST]
                    start_quiz("csv", chunk, csv_test_id=t_id)
                    st.rerun()
        with c:
            if mode != "manual":
                if st.button("📚 Testlar", use_container_width=True):
                    st.session_state.result_saved = False
                    st.session_state.quiz_page = "csv_list"
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_answers = []
                    st.session_state.current_q = None
                    st.session_state.current_q_id = None
                    st.session_state.q_choice = None
                    st.session_state.pop("q_choice_widget", None)
                    st.rerun()


# =============================================================================
# SECTION: STATS
# =============================================================================
elif st.session_state.student_section == "stats":
    st.markdown("### 📊 Statistika")

    # ✅ 2 ta tugma: manual vs csv
    s1, s2 = st.columns(2)
    with s1:
        if st.button("🧑‍💻 Mening so‘zlarim", use_container_width=True,
                     type="primary" if st.session_state.stats_view == "manual" else "secondary"):
            st.session_state.stats_view = "manual"
            st.rerun()
    with s2:
        if st.button("📚 CSV testlar", use_container_width=True,
                     type="primary" if st.session_state.stats_view == "csv" else "secondary"):
            st.session_state.stats_view = "csv"
            st.rerun()

    st.write("")
    stats_obj = st.session_state.stats_obj

    if st.session_state.stats_view == "manual":
        m = stats_obj.get("manual", {})
        m_attempts = int(m.get("attempts", 0))
        m_total = int(m.get("total_q", 0))
        m_correct = int(m.get("correct_q", 0))
        m_wrong = m_total - m_correct
        m_pct = acc_pct(m_correct, m_total)

        st.markdown("<div class='card'><b>🧑‍💻 Mening so‘zlarim statistikasi</b><div class='muted'>umumiy natijalar</div></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Testlar", m_attempts)
        c2.metric("Savollar", m_total)
        c3.metric("To‘g‘ri", m_correct)
        c4.metric("Aniqlik", f"{m_pct:.1f}%")

    else:
        st.markdown("<div class='card'><b>📚 CSV testlar statistikasi</b><div class='muted'>Test-1, Test-2 ...</div></div>", unsafe_allow_html=True)

        tests = stats_obj.get("csv", {}).get("tests", {})
        if not st.session_state.base_map:
            st.warning("CSV yuklanmagan.")
        else:
            csv_keys_sorted = sorted(st.session_state.base_map.keys())
            total_tests = (len(csv_keys_sorted) + QUESTIONS_PER_TEST - 1) // QUESTIONS_PER_TEST

            rows = []
            for t_id in range(1, total_tests + 1):
                s = tests.get(str(t_id))
                if s and int(s.get("total_q", 0)) > 0:
                    tot = int(s.get("total_q", 0))
                    cor = int(s.get("correct_q", 0))
                    att = int(s.get("attempts", 0))
                    rows.append({
                        "Test": f"Test-{t_id}",
                        "Urinish": att,
                        "To‘g‘ri": cor,
                        "Noto‘g‘ri": tot - cor,
                        "Aniqlik": f"{acc_pct(cor, tot):.1f}%"
                    })
                else:
                    rows.append({
                        "Test": f"Test-{t_id}",
                        "Urinish": 0,
                        "To‘g‘ri": 0,
                        "Noto‘g‘ri": 0,
                        "Aniqlik": "-"
                    })

            st.dataframe(rows, use_container_width=True, hide_index=True)

    st.write("")
    if st.button("🧹 Statistikani tozalash", use_container_width=True):
        st.session_state.stats_obj = {"manual": {"attempts": 0, "total_q": 0, "correct_q": 0}, "csv": {"tests": {}}}
        save_stats(st.session_state.stats_obj)
        st.success("Tozalandi ✅")
