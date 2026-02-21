import streamlit as st
from auth import upsert_user, is_valid_uz_phone

st.set_page_config(page_title="Login — Lug'at Pro", page_icon="🔐", layout="wide")

st.markdown("## 🔐 Ro‘yxatdan o‘tish / Kirish")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    st.success("✅ Siz allaqachon tizimdasiz.")
    if st.button("🏠 Home ga o‘tish", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

with st.form("login_form", clear_on_submit=False):
    first = st.text_input("Ism", placeholder="Suhrob")
    last = st.text_input("Familiya", placeholder="Panjiyev")
    phone = st.text_input("Telefon (+998901234567)", placeholder="+998...")
    ok = st.form_submit_button("✅ Login", use_container_width=True)

if ok:
    if not first.strip() or not last.strip():
        st.error("Ism va familiya kerak.")
    elif not is_valid_uz_phone(phone):
        st.error("Telefon formati noto‘g‘ri. Masalan: +998901234567")
    else:
        u = upsert_user(first, last, phone)
        st.session_state.user = u
        st.success("Login bo‘ldi ✅")
        st.switch_page("app.py")