import streamlit as st

from core.db import init_db
init_db()

st.set_page_config(
    page_title="Lug'at Pro — Home",
    page_icon="📘",
    layout="wide",
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 📘 Lug'at Pro")
    st.caption("English learning tool • MVP")

    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

    if st.button("🎓 Student (Test)", use_container_width=True):
        st.switch_page("pages/1_Student.py")

    if st.button("👨‍🏫 Teacher", use_container_width=True):
        st.switch_page("pages/2_Teacher.py")

    if st.button("👤 Sayt haqida", use_container_width=True):
        st.switch_page("pages/3_About.py")
    if st.button("👤 Profil", use_container_width=True):
        st.switch_page("pages/4_Profile.py")
    # faqat admin ko'rsin
    admin_phones = st.secrets.get("ADMIN_PHONES", [])
    me = st.session_state.get("user") or {}
    if (me.get("phone") or "") in admin_phones:
        if st.button("🛡️ Admin", use_container_width=True):
            st.switch_page("pages/5_Admin.py")
    if st.button("🛡️ Admin", use_container_width=True):
        st.switch_page("pages/5_Admin_Login.py")
        
    st.divider()
    st.caption("© 2026 • Built by Suhrob")


# ---------- Home content ----------
st.markdown(
    """
    <style>
      .hero {
        padding: 28px 28px;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(80,120,255,0.18), rgba(0,0,0,0));
        border: 1px solid rgba(255,255,255,0.08);
      }

      .bigtitle { 
        font-size: 44px; 
        font-weight: 800; 
        line-height: 1.1; 
        margin-bottom: 10px; 
      }

      .subtitle { 
        font-size: 18px; 
        opacity: 0.9; 
        margin-bottom: 18px; 
      }

      .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.12);
        opacity: 0.9;
        margin-right: 8px;
        margin-bottom: 8px;
        font-size: 13px;
      }

      .card {
        padding: 18px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        height: 100%;
      }

      /* 📱 Telefon uchun */
      @media (max-width: 768px) {
        .hero {
          padding: 18px;
        }

        .bigtitle {
          font-size: 28px;
        }

        .subtitle {
          font-size: 15px;
        }

        .pill {
          font-size: 12px;
          padding: 5px 8px;
        }
      }
    </style>
    """,
    unsafe_allow_html=True
)

from auth import upsert_user, is_valid_uz_phone, norm_phone

st.write("")
st.markdown("## 🔐 Ro'yxatdan o'tish / Kirish ")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    u = st.session_state.user
    st.success(f"✅ Tizimga kirdingiz.")

else:
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
            st.rerun()


st.markdown(
    """
    <div class="hero">
      <div class="bigtitle">📘 Lug'at Pro</div>
      <div class="subtitle">
        Lug'at yodlash va test qilishni osonlashtiradigan mini platforma.
        O‘quv markazlar uchun ham qulay.
      </div>
      <span class="pill">✅ CSV dataset</span>
      <span class="pill">✅ Suggestions</span>
      <span class="pill">✅ Student tests</span>
      <span class="pill">🔒 Teacher AI (Premium)</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
colA, colB, colC = st.columns([1.2, 1, 1])

with colA:
    st.markdown(
        """
        <div class="card">
          <h3>🎓 Student</h3>
          <p>
            So‘z qo‘shing, test ishlang, CSV testlar bilan mashq qiling.
            Tez va oddiy.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Student bo‘limiga o‘tish ➜", type="primary", use_container_width=True):
        st.switch_page("pages/1_Student.py")

with colB:
    st.markdown(
        """
        <div class="card">
          <h3>👨‍🏫 Teacher</h3>
          <p>
            Grammar bo‘yicha tarqatma material generator (hozircha premium).
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Teacher bo‘limiga o‘tish ➜", use_container_width=True):
        st.switch_page("pages/2_Teacher.py")

with colC:
    st.markdown(
        """
        <div class="card">
          <h3>👤 Sayt haqida</h3>
          <p>
            Loyihani kim qilgan? Kontaktlar, GitHub, Telegram va boshqalar.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("About ➜", use_container_width=True):
        st.switch_page("pages/3_About.py")

st.write("")
st.info("💡 Tavsiya: chap sidebar orqali bo‘limlarni tez almashtiring.")
