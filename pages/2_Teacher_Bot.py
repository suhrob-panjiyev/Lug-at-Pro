import os
import requests
import pandas as pd
import streamlit as st

from pages.student_core import require_login, render_sidebar, inject_student_css
import json

def safe_json(resp):
    """Response JSON bo'lmasa ham yiqitmaydi; xatoni tushunarli qiladi."""
    try:
        return resp.json(), None
    except Exception:
        txt = (resp.text or "")[:800]
        return None, f"JSON emas (status={resp.status_code}). Javob (1-qismi):\n{txt}"
    
require_login()
st.set_page_config(page_title="Teacher — Bot", page_icon="🤖", layout="wide")
render_sidebar(active="teacher")
inject_student_css()

BOT_API = "https://lugatpro-bot.onrender.com"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
HEADERS = {"X-API-Key": ADMIN_API_KEY} if ADMIN_API_KEY else {}

st.title("🤖 Bot orqali topshiriq")
st.caption("Test yaratish va Telegram guruhga bot orqali yuborish.")


# ---- KPI
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🤖 Telegram Bot — Monitoring</div>', unsafe_allow_html=True)

k = {"classes": 0, "students": 0, "assignments": 0, "attempts": 0, "avg_pct": 0.0}
try:
    k = requests.get(f"{BOT_API}/api/bot/kpis", headers=HEADERS, timeout=60).json()
except Exception:
    st.warning("Bot server javob bermayapti (sleep/cold start bo‘lishi mumkin). KPI vaqtincha ko‘rinmaydi, lekin sahifa ishlayveradi.")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Classes", k.get("classes", 0))
c2.metric("Students", k.get("students", 0))
c3.metric("Assignments", k.get("assignments", 0))
c4.metric("Attempts", k.get("attempts", 0))
c5.metric("Avg %", f"{float(k.get('avg_pct', 0.0)):.1f}%")

st.markdown("</div>", unsafe_allow_html=True)
try:
    k = requests.get(f"{BOT_API}/api/bot/kpis", headers=HEADERS, timeout=60).json()
except Exception:
    st.warning("Bot server javob bermayapti (sleep bo‘lishi mumkin). 1-2 daqiqadan keyin qayta urinib ko‘ring.")
    st.stop()

# ---- Create class
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">➕ Class yaratish</div>', unsafe_allow_html=True)

with st.form("create_class_form"):
    name = st.text_input("Class nomi (masalan: IT-101)")
    group_id = st.number_input("Telegram group_id", step=1, format="%d")
    teacher_id = st.number_input("Teacher ID (botda admin/teacher user_id)", step=1, format="%d")
    submitted = st.form_submit_button("Create class")

if submitted:
    try:
        r = requests.post(
            f"{BOT_API}/api/classes/create",
            headers=HEADERS,
            json={"name": name, "group_id": int(group_id), "teacher_id": int(teacher_id)},
            timeout=60,
        )
        if r.status_code != 200:
            st.error(f"Xato: {r.status_code} — {r.text}")
        else:
            st.success(f"Class yaratildi ✅ (id={r.json().get('class_id')})")
            st.rerun()
    except Exception as e:
        st.error(f"Ulanishda xato: {e}")

st.markdown("</div>", unsafe_allow_html=True)

# ---- Classes
resp = requests.get(f"{BOT_API}/api/classes", headers=HEADERS, timeout=60)
data, err = safe_json(resp)

if err:
    st.error("Bot API /api/classes JSON qaytarmadi.")
    st.code(err)
    st.stop()

classes = data
# ---- normalize classes payload ----
# Kutilgan format: list[dict]
if isinstance(classes, dict):
    # FastAPI error: {"detail": "..."} yoki wrapper: {"data": [...]}
    if "data" in classes and isinstance(classes["data"], list):
        classes = classes["data"]
    else:
        st.error("Bot API /api/classes kutilmagan format qaytardi (list emas).")
        st.json(classes)
        st.stop()

if not isinstance(classes, list):
    st.error("Bot API /api/classes list qaytarmadi.")
    st.write(type(classes))
    st.stop()

# list bo‘lsa ham elementlari dict ekanini tekshiramiz
if len(classes) > 0 and not isinstance(classes[0], dict):
    st.error("Bot API /api/classes list ichida dict emas.")
    st.write(type(classes[0]))
    st.stop()
dfc = pd.DataFrame.from_records(classes) if classes else pd.DataFrame()

if dfc.empty:
    st.info("Hozircha bot DB’da class yo‘q (yoki API key noto‘g‘ri).")
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
try:
    classes = requests.get(f"{BOT_API}/api/classes", headers=HEADERS, timeout=60).json()
except Exception:
    st.warning("Bot serverga ulana olmadik. Botni uyg‘otish uchun /health ni ochib ko‘ring.")
    st.stop()

# ---- Create assignment
st.write("")
st.markdown("### ➕ Topshiriq yaratish (Web → Bot)")

with st.form("create_assignment_form"):
    n_questions = st.number_input("Savollar soni", min_value=1, max_value=50, value=10, step=1)
    deadline_hhmm = st.text_input("Deadline (HH:MM) ixtiyoriy", value="23:59")
    deactivate_prev = st.checkbox("Oldingi topshiriq(lar)ni o‘chirib, faqat yangisini Active qil", value=True)

    submitted = st.form_submit_button("✅ Test yaratish")

if submitted:
    dh = deadline_hhmm.strip() or None
    if dh is not None:
        ok = (len(dh) == 5 and dh[2] == ":" and dh[:2].isdigit() and dh[3:].isdigit())
        if not ok:
            st.error("Deadline formati noto‘g‘ri. Masalan: 18:30")
            st.stop()

    resp = requests.post(
        f"{BOT_API}/api/assignments/create",
        headers=HEADERS,
        json={
            "class_id": int(class_id),
            "n_questions": int(n_questions),
            "deadline_hhmm": dh,
            "deactivate_prev": deactivate_prev,
        },
        timeout=30,
    ).json()

    if resp.get("ok"):
        st.success(f"✅ Test yaratildi! ID={resp['assignment_id']}")
        st.rerun()
    else:
        st.error(resp)