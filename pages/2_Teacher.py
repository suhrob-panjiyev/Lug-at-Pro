import streamlit as st

st.set_page_config(page_title="Teacher", page_icon="👨‍🏫", layout="centered")

with st.sidebar:
    st.markdown("## 📘 Lug'at Pro")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    if st.button("🎓 Student (Test)", use_container_width=True):
        st.switch_page("pages/1_Student.py")
    if st.button("👨‍🏫 Teacher", use_container_width=True):
        st.switch_page("pages/2_Teacher.py")
    if st.button("👤 Sayt haqida", use_container_width=True):
        st.switch_page("pages/3_About.py")

st.title("👨‍🏫 Ustoz bo‘limi — Grammar Material Generator")

with st.expander("⚙️ Sozlamalar", expanded=True):
    topic = st.text_input("Grammar mavzu", placeholder="Present Simple")
    level = st.selectbox("Daraja", ["A1", "A2", "B1", "B2"])
    minutes = st.selectbox("Dars vaqti", [30, 45, 60, 90], index=1)
    language = st.selectbox("Tushuntirish tili", ["Uzbek", "Russian", "English"], index=0)

col1, col2 = st.columns(2)
with col1:
    generate_clicked = st.button("✨ Material yaratish", type="primary", use_container_width=True)
with col2:
    clear_clicked = st.button("🧹 Tozalash", use_container_width=True)

if generate_clicked:
    st.info(
        """
### 🤖 AI Grammar Material Generator

Bu modul professional AI modeli orqali avtomatik
grammar handout (tarqatma material) yaratadi.

🔒 Hozircha API billing yoqilmaganligi sababli vaqtincha o‘chiq.

To‘lov (≈ $5) qo‘shilgandan so‘ng:
- Professional tushuntirish
- Mashqlar
- Answer key
- 1–2 betlik tayyor handout

avtomatik generatsiya qilinadi.
"""
    )

if clear_clicked:
    st.rerun()
