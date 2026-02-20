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

@st.cache_resource
def get_model():
    return load_model()

model = get_model()

@st.cache_data(show_spinner=False)
def predict_batch(words_norm: list[str]) -> list[str]:
    return model.predict(words_norm).tolist()

# 1) CSV + user so'zlarini jamlaymiz (unique)
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

# 2) Summary
counts = df["Level"].value_counts().reindex(LEVELS).fillna(0).astype(int)
c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, lv in zip([c1, c2, c3, c4, c5, c6], LEVELS):
    col.metric(lv, int(counts[lv]))

st.divider()

# 3) Filter
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

st.write(f"**{pick_level}** darajadagi so‘zlar: **{len(dff)}** ta")
st.dataframe(dff[["English", "Level"]], use_container_width=True, hide_index=True)

st.write("")
colA, colB = st.columns([1.3, 1])

with colA:
    if st.button(f"📝 {pick_level} darajadan test boshlash", type="primary", use_container_width=True, disabled=(len(dff) < 2)):
        level_keys = dff["key"].tolist()
        random.shuffle(level_keys)
        level_keys = level_keys[:QUESTIONS_PER_TEST] if len(level_keys) >= QUESTIONS_PER_TEST else level_keys

        # test sahifasiga "level" mode bilan yuboramiz
        start_quiz("level", level_keys)
        st.switch_page("pages/1_2_test.py")

with colB:
    st.caption("Eslatma: darajalar AI taxminiga asoslanadi (MVP).")