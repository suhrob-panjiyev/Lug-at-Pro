import streamlit as st

from pages.student_core import require_login

# LLM providerlar
from llm_openai import generate_grammar_handout as openai_handout
from llm_gemini import generate_grammar_handout as gemini_handout

require_login()

st.set_page_config(page_title="Teacher", page_icon="👨‍🏫", layout="wide")

import os

st.markdown("### 🔎 Debug (vaqtincha)")
key_from_secrets = st.secrets.get("GEMINI_API_KEY", "")
key_from_env = os.getenv("GEMINI_API_KEY", "")

st.write("GEMINI_API_KEY in st.secrets:", "✅ bor" if key_from_secrets else "❌ yo‘q")
st.write("GEMINI_API_KEY in env:", "✅ bor" if key_from_env else "❌ yo‘q")

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 📘 Lug'at Pro")
    st.caption("Teacher bo‘limi")

    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    if st.button("🎓 Student", use_container_width=True):
        st.switch_page("pages/1_Student.py")
    if st.button("👨‍🏫 Teacher", use_container_width=True):
        st.switch_page("pages/2_Teacher.py")
    if st.button("👤 Sayt haqida", use_container_width=True):
        st.switch_page("pages/3_About.py")

st.title("👨‍🏫 Teacher — Grammar Material Generator")

# ---------- State ----------
if "teacher_out_md" not in st.session_state:
    st.session_state.teacher_out_md = ""

# ---------- Settings ----------
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("⚙️ Sozlamalar")

    provider = st.selectbox("AI Provider", ["Gemini", "OpenAI"], index=0)

    topic = st.text_input("Grammar mavzu", placeholder="Present Simple")
    level = st.selectbox("Daraja", ["A1", "A2", "B1", "B2", "C1", "C2"], index=2)
    minutes = st.selectbox("Dars vaqti (minut)", [30, 45, 60, 90], index=1)
    language = st.selectbox("Tushuntirish tili", ["Uzbek", "Russian", "English"], index=0)

    c1, c2, c3 = st.columns(3)
    with c1:
        generate_clicked = st.button("✨ Material yaratish", type="primary", use_container_width=True)
    with c2:
        clear_clicked = st.button("🧹 Tozalash", use_container_width=True)
    with c3:
        example_clicked = st.button("⚡ Misol", use_container_width=True)

    if example_clicked:
        st.session_state.teacher_topic = "Present Perfect vs Past Simple"
        st.rerun()

    if clear_clicked:
        st.session_state.teacher_out_md = ""
        st.rerun()

    st.markdown("---")
    st.caption("🔐 API key bo‘lmasa generator ishlamaydi. Pastda qanday qo‘yishni yozib berdim.")

with right:
    st.subheader("📄 Natija (Markdown)")

    if st.session_state.teacher_out_md:
        st.markdown(st.session_state.teacher_out_md)

        st.download_button(
            "⬇️ Markdown yuklab olish",
            data=st.session_state.teacher_out_md,
            file_name=f"handout_{topic.strip().replace(' ', '_') or 'grammar'}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.info("Hali material yo‘q. Chap tomonda sozlamalarni kiriting va **Material yaratish** ni bosing.")

# ---------- Generate ----------
if generate_clicked:
    topic = (topic or "").strip()
    if not topic:
        st.warning("Iltimos, grammar mavzuni kiriting 🙂")
        st.stop()

    with st.spinner("AI material tayyorlayapti..."):
        try:
            if provider == "OpenAI":
                out = openai_handout(topic=topic, level=level, minutes=int(minutes), language=language)
            else:
                out = gemini_handout(topic=topic, level=level, minutes=int(minutes), language=language)

            st.session_state.teacher_out_md = out
            st.success("✅ Tayyor!")
            st.rerun()

        except Exception as e:
            st.error("❌ Generator ishlamadi. Sabab (qisqa):")
            st.code(str(e))
            st.info(
                "Ko‘pincha sabab: API KEY qo‘yilmagan yoki noto‘g‘ri. "
                "Quyida secrets.toml qanday bo‘lishi kerakligini ko‘ring."
            )