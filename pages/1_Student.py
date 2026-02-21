import streamlit as st
from pages.student_core import require_login

st.set_page_config(page_title="Student — Lug'at Pro", page_icon="🎓", layout="wide")

require_login()

# "Student" menyusidan kirilganda doim shu sahifadan boshlansin:
st.switch_page("pages/1_1_suz_qushish.py")