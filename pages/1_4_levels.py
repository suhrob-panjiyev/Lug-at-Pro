import streamlit as st
import pandas as pd
import random

from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav,
    QUESTIONS_PER_TEST, norm_en, start_quiz
)

from ai.cefr.infer import load_model

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

st.set_page_config(page_title="Student — Levels", page_icon="📚", layout="wide")
render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav(active="levels", page_key="levels")

st.markdown("### 📚 AI: So‘zlarni darajalarga ajratish (A1–C2)")
st.caption("Eslatma: darajalar AI taxminiga asoslanadi (MVP).")

# -------------------------
# Model
# -------------------------
@st.cache_resource
def get_model():
    return load_model()

model = get_model()

@st.cache_data(show_spinner=False)
def predict_batch(words_norm: list[str]) -> list[str]:
    return model.predict(words_norm).tolist()

# -------------------------
# 1) CSV + user so'zlarini jamlaymiz (unique)
# -------------------------
all_map = {}
for k, v in st.session_state.base_map.items():
    all_map[k] = v["en"]
for k, v in st.session_state.user_map.items():
    all_map[k] = v["en"]

keys = list(all_map.keys())
words = [all_map[k] for k in keys]
words_norm = [norm_en(w) for w in words]

levels = predict_batch(words_norm)
df = pd.DataFrame({"key": keys, "English": words, "Level": levels})

# -------------------------
# 2) Summary (A1..C2 count)
# -------------------------
counts = df["Level"].value_counts().reindex(LEVELS).fillna(0).astype(int)
c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, lv in zip([c1, c2, c3, c4, c5, c6], LEVELS):
    col.metric(lv, int(counts[lv]))

st.divider()

# -------------------------
# 3) Filter: level + source
# -------------------------
left, right = st.columns([1.2, 1])
with left:
    pick_level = st.selectbox("Darajani tanlang:", LEVELS, index=2)  # B1
with right:
    source = st.selectbox("Qaysi bazadan?", ["Hammasi", "Faqat CSV", "Faqat user"], index=0)

dff = df[df["Level"] == pick_level].copy()

if source == "Faqat CSV":
    dff = dff[dff["key"].isin(st.session_state.base_map.keys())]
elif source == "Faqat user":
    dff = dff[dff["key"].isin(st.session_state.user_map.keys())]

total = len(dff)
st.write(f"**{pick_level}** darajadagi so‘zlar: **{total}** ta")

st.write("")

# -------------------------
# 4) Two main actions (buttons)
# -------------------------
b1, b2 = st.columns(2)

with b1:
    do_test = st.button(
        f"📝 {pick_level} darajadan test boshlash",
        type="primary",
        use_container_width=True,
        disabled=(total < 2)
    )

with b2:
    show_list = st.button(
        f"📋 {pick_level} so‘zlar ro‘yxatini ko‘rish",
        use_container_width=True,
        disabled=(total == 0)
    )

# test action
if do_test:
    level_keys = dff["key"].tolist()
    random.shuffle(level_keys)
    level_keys = level_keys[:QUESTIONS_PER_TEST] if len(level_keys) >= QUESTIONS_PER_TEST else level_keys

    start_quiz("level", level_keys)
    st.switch_page("pages/1_2_test.py")

# -------------------------
# 5) List section (only when requested)
# -------------------------
if "levels_show_list" not in st.session_state:
    st.session_state.levels_show_list = False

if show_list:
    st.session_state.levels_show_list = True

if st.session_state.levels_show_list:
    st.write("")
    with st.expander(f"📋 {pick_level} ro‘yxati", expanded=True):
        q = st.text_input("🔎 Qidirish (ro‘yxat ichida)", value="", placeholder="fire, memory ...")

        list_df = dff.copy()
        if q.strip():
            qq = q.strip().lower()
            list_df = list_df[list_df["English"].str.lower().str.contains(qq)]

        st.write(f"Ko‘rsatilmoqda: **{len(list_df)}** ta")

        st.dataframe(
            list_df[["English"]],
            use_container_width=True,
            hide_index=True,
            height=520
        )

        csv_bytes = list_df[["English", "Level"]].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Shu ro‘yxatni CSV qilib olish",
            data=csv_bytes,
            file_name=f"cefr_{pick_level}_list.csv",
            mime="text/csv",
            use_container_width=True
        )

        c_close = st.button("❌ Ro‘yxatni yopish", use_container_width=True)
        if c_close:
            st.session_state.levels_show_list = False
            st.rerun()