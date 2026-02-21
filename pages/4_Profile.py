import streamlit as st
import hashlib
from datetime import datetime

from pages.student_core import render_sidebar
from core.user_repo_db import get_user_by_phone


st.set_page_config(page_title="Profil", page_icon="👤", layout="wide")
render_sidebar(active="student")  # sidebar style bir xil bo'lib turadi

st.markdown("## 👤 Profil")

# Orqaga tugmasi (Home ga)
top_left, top_right = st.columns([1, 5])

with top_left:
    if st.button("⬅️ Orqaga", use_container_width=True):
        st.switch_page("app.py")

with top_right:
    st.empty()

# ---------------------------
# Guard
# ---------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.warning("Profilni ko‘rish uchun avval login qiling.")
    st.switch_page("app.py")

u = st.session_state.user

# ---------------------------
# Avatar generator (deterministik)
# ---------------------------
EMOJIS = ["🦊", "🐯", "🐼", "🦁", "🐸", "🐵", "🐙", "🦉", "🐺", "🐨", "🐧", "🐝", "🦄", "🐲"]
COLORS = ["#ff4757", "#ffa502", "#2ed573", "#1e90ff", "#3742fa", "#a55eea", "#ff6b81", "#7bed9f"]

def stable_hash(s: str) -> int:
    h = hashlib.sha256((s or "").encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def build_avatar(phone: str):
    x = stable_hash(phone)
    emoji = EMOJIS[x % len(EMOJIS)]
    color = COLORS[(x // 7) % len(COLORS)]
    return emoji, color

emoji, color = build_avatar(u.get("phone", ""))

st.markdown(
    f"""
    <style>
      .profile-card {{
        padding: 18px;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.03);
      }}
      .avatar {{
        width: 84px;
        height: 84px;
        border-radius: 20px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-size: 44px;
        background: {color}22;
        border: 1px solid {color}66;
      }}
      .muted {{ opacity: 0.82; }}
      .row {{
        display:flex;
        gap: 16px;
        align-items:center;
      }}
      @media (max-width: 768px) {{
        .row {{ flex-direction: column; align-items:flex-start; }}
        .avatar {{ width: 72px; height: 72px; font-size: 40px; }}
      }}
    </style>

    <div class="profile-card">
      <div class="row">
        <div class="avatar">{emoji}</div>
        <div>
          <div style="font-size:26px; font-weight:800; line-height:1.1;">
            {u.get("first_name","")} {u.get("last_name","")}
          </div>
          <div class="muted" style="margin-top:6px;">
            Telefon: <b>{u.get("phone","")}</b>
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# ---------------------------
# Extra info (DB dan real holatini ko'rsatamiz)
# ---------------------------
db_user = get_user_by_phone(u.get("phone", "")) or u

def fmt_dt(s: str):
    if not s:
        return "-"
    return str(s).replace("T", " ").replace("Z", "")

c1, c2, c3 = st.columns(3)
c1.metric("Ro‘yxatdan o‘tgan", fmt_dt(db_user.get("created_at", "")))
c2.metric("Oxirgi login", fmt_dt(db_user.get("last_login_at", "")))
c3.metric("ID", db_user.get("phone", "-"))

st.divider()

# ---------------------------
# Actions
# ---------------------------
a, b = st.columns([1.3, 1])
with a:
    if st.button("🎓 Student bo‘limiga o‘tish", type="primary", use_container_width=True):
        st.switch_page("pages/1_Student.py")

with b:
    if st.button("🚪 Chiqish (logout)", use_container_width=True):
        st.session_state.user = None
        st.switch_page("app.py")