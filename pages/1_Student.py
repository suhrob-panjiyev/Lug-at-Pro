import streamlit as st
from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav
)

st.set_page_config(page_title="Student — Lug'at Pro", page_icon="🎓", layout="wide")

render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav()

# section router
if st.session_state.student_section == "add":
    st.switch_page("pages/1_1_suz_qushish.py")
elif st.session_state.student_section == "test":
    st.switch_page("pages/1_2_test.py")
else:
    st.switch_page("pages/1_3_statistika.py")
