import streamlit as st
from streamlit_searchbox import st_searchbox
import random
import json
import csv
from pathlib import Path
import requests
import pandas as pd
from typing import Optional, List
from datetime import datetime

# ✅ NEW imports
from gtts import gTTS
import io
import base64

# ✅ 3) SAVE PATCH: DB repo import
from core.word_repo_db import upsert_word, get_user_words_map

from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav,
    norm_en, suggestions, translate_mymemory, is_weird_translation
)
from pages.student_core import require_login

require_login()
st.set_page_config(page_title="Student — So‘z qo‘shish", page_icon="➕", layout="wide")

render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav(active="add", page_key="add")

st.markdown("### ➕ So‘z qo‘shish")

# ---- state init ----
if "en_input" not in st.session_state:
    st.session_state.en_input = ""
if "last_translations" not in st.session_state:
    st.session_state.last_translations = []

# ✅ NEW state (pronunciation)
if "pron_word" not in st.session_state:
    st.session_state.pron_word = ""
if "pron_play" not in st.session_state:
    st.session_state.pron_play = False


# ✅ NEW: cached TTS bytes
@st.cache_data(show_spinner=False)
def tts_mp3_bytes(word: str) -> bytes:
    word = (word or "").strip()
    if not word:
        return b""
    tts = gTTS(text=word, lang="en")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()


# ---------------------------
# 1) SINGLE INPUT: live searchbox
# ---------------------------
def search_fn(q: str):
    q = (q or "").strip()
    if not q:
        return []

    # bazadan tavsiyalar
    sug = suggestions(q, st.session_state.english_list_csv, limit=16)

    # ✅ user typed so‘z ham birinchi bo‘lsin
    if q and all(q.lower() != s.lower() for s in sug):
        sug = [q] + sug
    else:
        q_low = q.lower()
        sug_sorted = [q]
        for s in sug:
            if s.lower() != q_low:
                sug_sorted.append(s)
        sug = sug_sorted

    # dedupe
    seen = set()
    out = []
    for w in sug:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw)
            out.append(w)

    return out[:16]


# ✅ Input + 🔊 button yonma-yon
col_inp, col_audio = st.columns([8, 1.3], vertical_alignment="bottom")

with col_inp:
    picked = st_searchbox(
        search_fn,
        key="en_live",
        placeholder="car, app, apple ...",
        label="English so‘zni yozing"
    )

en_word = (picked or "").strip()

with col_audio:
    # 🔊 tugma faqat so‘z bor bo‘lsa aktiv
    play_click = st.button(
        "🔊",
        help="Talaffuzni eshitish",
        use_container_width=True,
        disabled=not bool(en_word)
    )
    if play_click and en_word:
        st.session_state.pron_word = en_word
        st.session_state.pron_play = True


# statega yozib qo‘yamiz (keyingi bo‘limlar uchun)
if en_word:
    st.session_state.en_input = en_word

en_key = norm_en(en_word)


# ✅ Audio chiqishi (player ko‘rinmaydi)
if st.session_state.pron_play and st.session_state.pron_word == en_word:
    try:
        audio_bytes = tts_mp3_bytes(en_word)
        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode()
            st.markdown(
                f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """,
                unsafe_allow_html=True
            )

            # ✅ MUHIM: bir marta chalinsa flagni o‘chir
            st.session_state.pron_play = False

    except Exception as e:
        st.error(f"Talaffuz xatosi: {e}")
        st.session_state.pron_play = False

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

    # ✅ 3.1 CSV’dan topilgan so‘z save joyi (DB)
    if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(len(selected) == 0)):
        u = st.session_state.user
        user_id = int(u["id"])

        upsert_word(user_id, item["en"], selected)
        st.session_state.user_map = get_user_words_map(user_id)
        st.success("Saqlandi ✅")

# ---------------------------
# CSV’da yo‘q bo‘lsa
# ---------------------------
else:
    st.info("Bu so‘z bazada yo‘q. Istasangiz avtomatik tarjima qilib saqlaysiz.")

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

    # ✅ 3.2 Avto tarjima save joyi (DB)
    if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(not en_word or len(selected) == 0)):
        u = st.session_state.user
        user_id = int(u["id"])

        upsert_word(user_id, en_word, selected)
        st.session_state.user_map = get_user_words_map(user_id)
        st.success("Saqlandi ✅")

# ---------------------------
# Footer
# ---------------------------
k1, k2 = st.columns(2)
k1.metric("User so‘zlari", len(st.session_state.user_map))
k2.metric("CSV so‘zlari", len(st.session_state.base_map))