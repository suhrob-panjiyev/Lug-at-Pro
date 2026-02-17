import streamlit as st

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

    if st.button("👤 Men haqimda", use_container_width=True):
        st.switch_page("pages/3_About.py")

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
      .bigtitle { font-size: 44px; font-weight: 800; line-height: 1.1; margin-bottom: 10px; }
      .subtitle { font-size: 18px; opacity: 0.9; margin-bottom: 18px; }
      .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.12);
        opacity: 0.9;
        margin-right: 8px;
        font-size: 13px;
      }
      .card {
        padding: 18px;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        height: 100%;
      }
    </style>
    """,
    unsafe_allow_html=True
)

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
          <h3>👤 Men haqimda</h3>
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
