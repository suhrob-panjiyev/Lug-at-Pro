import streamlit as st
from pages.student_core import require_login, render_sidebar, inject_student_css

import streamlit as st
import pandas as pd
from core.db import init_db
init_db()

from core.bot_admin_repo_db import ensure_bot_db
ensure_bot_db()

from core.admin_repo_db import (
    list_users_with_metrics,
    get_user_attempts,
    get_user_attempts_summary,
)

from core.bot_admin_repo_db import (
    bot_kpis,
    list_classes,
    list_assignments,
    list_attempts,
    daily_top,
    weekly_top,
    create_assignment_web,
    set_assignment_active,
)


# ✅ SHU IMPORTLARNI 5_Admin.py DAN KO‘CHIRING:
# from core.bot_admin_repo_db import bot_kpis, list_classes, create_assignment_web
# yoki sizda qanday bo'lsa, o'shani qo'ying

require_login()
st.set_page_config(page_title="Teacher — Bot", page_icon="🤖", layout="wide")
render_sidebar(active="teacher")
inject_student_css()

st.title("🤖 Bot orqali topshiriq")
st.caption("Test yaratish va Telegram guruhga bot orqali yuborish.")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🤖 Telegram Bot — Monitoring</div>', unsafe_allow_html=True)

k = bot_kpis()
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Classes", k["classes"])
k2.metric("Students", k["students"])
k3.metric("Assignments", k["assignments"])
k4.metric("Attempts", k["attempts"])
k5.metric("Avg %", f"{k['avg_pct']:.1f}%")
st.markdown("</div>", unsafe_allow_html=True)

st.write("")
dfc = list_classes()
if dfc.empty:
    st.info("Hozircha bot DB’da class yo‘q.")
    st.stop()

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🏫 Sinflar</div>', unsafe_allow_html=True)

st.dataframe(
    dfc.rename(columns={
        "id": "ID",
        "name": "Nomi",
        "group_id": "Group ID",
        "teacher_id": "Teacher ID",
        "created_at": "Yaratilgan",
        "members_count": "A’zolar",
        "assignments_count": "Topshiriqlar",
        "attempts_count": "Urinishlar",
        "xp_sum": "Jami XP",
    }),
    use_container_width=True,
    hide_index=True,
)

class_id = st.selectbox(
    "Sinf tanlang",
    options=dfc["id"].tolist(),
    format_func=lambda cid: f"{int(cid)} — {dfc.loc[dfc['id']==cid,'name'].values[0]}",
)
st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# ✅ Assignment yaratish form (Web → Bot)
# ============================================================
st.write("")
st.markdown("### ➕ Topshiriq yaratish (Web → Bot)")

with st.form("create_assignment_form", clear_on_submit=False):
    n_questions = st.number_input(
        "Savollar soni ", min_value=1, max_value=50, value=10, step=1
    )
    deadline_hhmm = st.text_input(
        "Deadline (HH:MM) ixtiyoriy",
        value="23:59",
        help="Masalan: 18:30 yoki 23:59. Bo‘sh qoldirsangiz deadline bo‘lmaydi.",
    )
    deactivate_prev = st.checkbox(
        "Oldingi topshiriq(lar)ni o‘chirib, faqat yangisini Active qil", value=True
    )

    submitted = st.form_submit_button("✅ Test yaratish")
    st.success("Bu qisim hozrcha faqat localni ishlayapti, yani siz bu yerdan foydalana olmaysiz. 👈🏻👈🏻👈🏻")

    if submitted:
        dh = deadline_hhmm.strip() or None

        if dh is not None:
            ok = (len(dh) == 5 and dh[2] == ":" and dh[:2].isdigit() and dh[3:].isdigit())
            if not ok:
                st.error("Deadline formati noto‘g‘ri. Masalan: 18:30")
                st.stop()

        aid = create_assignment_web(int(class_id), int(n_questions), dh, deactivate_prev=deactivate_prev)
        st.success(f"✅ Test yaratildi! ID={aid}")
        st.rerun()