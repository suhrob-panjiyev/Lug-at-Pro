import streamlit as st


def render_sidebar(active: str = "student"):
    with st.sidebar:
        st.markdown("## 📘 Lug'at Pro")
        st.caption("Student bo‘limi")

        if st.button("🏠 Home", width="stretch"):
            st.switch_page("app.py")

        if st.button(
            "🎓 Student",
            width="stretch",
            type="primary" if active == "student" else "secondary",
        ):
            st.switch_page("pages/1_Student.py")

        if st.button("👨‍🏫 Teacher", width="stretch"):
            st.switch_page("pages/2_Teacher.py")

        if st.button("👤 Sayt haqida", width="stretch"):
            st.switch_page("pages/3_About.py")

        if st.button("👤 Profil", width="stretch"):
            st.switch_page("pages/4_Profile.py")
        if st.button("🛡️ Admin", use_container_width=True):
            st.switch_page("pages/5_Admin_Login.py")

        st.divider()
        st.caption("© 2026 • Built by Suhrob")


def inject_student_css():
    st.markdown(
        """
        <style>
          .hero{
            padding: 18px 18px;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.10);
            background: linear-gradient(135deg, rgba(80,120,255,0.20), rgba(0,0,0,0));
          }
          .pill{
            display:inline-block;
            padding:6px 10px;
            border-radius:999px;
            border:1px solid rgba(255,255,255,0.14);
            background: rgba(255,255,255,0.04);
            font-size:13px;
            margin-right:8px;
          }
          .card{
            padding: 14px 14px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.03);
          }
          .qa-card{
            padding: 14px 14px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.03);
            margin-bottom: 10px;
          }
          .muted{opacity:.82}
          .big{font-size:34px;font-weight:800;line-height:1.05}
          .sug-title{margin-top:8px;margin-bottom:6px}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <div class="hero">
          <div class="big">🎓 Student</div>
          <div class="muted" style="margin-top:6px">So‘z qo‘shing → test ishlang → natijani ko‘ring.</div>
          <div style="margin-top:10px">
            <span class="pill">✅ Tavsiya</span>
            <span class="pill">✅ 2 xil test</span>
            <span class="pill">✅ Statistika</span>
            <span class="pill">✅ Levels</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def render_top_nav(active: str = "add", page_key: str = "student"):
    """
    active: "add" | "test" | "stats" | "levels"
    page_key: unique prefix for widget keys
    """
    k_add = f"{page_key}_nav_add"
    k_test = f"{page_key}_nav_test"
    k_stats = f"{page_key}_nav_stats"
    k_levels = f"{page_key}_nav_levels"

    n1, n2, n3, n4 = st.columns(4)

    with n1:
        if st.button(
            "➕ So‘z qo‘shish",
            key=k_add,
            width="stretch",
            type="primary" if active == "add" else "secondary",
        ):
            st.switch_page("pages/1_1_suz_qushish.py")

    with n2:
        if st.button(
            "📝 Test",
            key=k_test,
            width="stretch",
            type="primary" if active == "test" else "secondary",
        ):
            st.switch_page("pages/1_2_test.py")

    with n3:
        if st.button(
            "📊 Statistika",
            key=k_stats,
            width="stretch",
            type="primary" if active == "stats" else "secondary",
        ):
            st.switch_page("pages/1_3_statistika.py")

    with n4:
        if st.button(
            "📚 Levels",
            key=k_levels,
            width="stretch",
            type="primary" if active == "levels" else "secondary",
        ):
            st.switch_page("pages/1_4_levels.py")