import streamlit as st
from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav,
    QUESTIONS_PER_TEST, acc_pct, save_stats
)

st.set_page_config(page_title="Student — Statistika", page_icon="📊", layout="wide")
render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav()

st.markdown("### 📊 Statistika")

s1, s2 = st.columns(2)
with s1:
    if st.button("🧑‍💻 Mening so‘zlarim", use_container_width=True,
                 type="primary" if st.session_state.stats_view == "manual" else "secondary"):
        st.session_state.stats_view = "manual"
        st.rerun()
with s2:
    if st.button("📚 CSV testlar", use_container_width=True,
                 type="primary" if st.session_state.stats_view == "csv" else "secondary"):
        st.session_state.stats_view = "csv"
        st.rerun()

st.write("")
stats_obj = st.session_state.stats_obj

if st.session_state.stats_view == "manual":
    m = stats_obj.get("manual", {})
    m_attempts = int(m.get("attempts", 0))
    m_total = int(m.get("total_q", 0))
    m_correct = int(m.get("correct_q", 0))
    m_pct = acc_pct(m_correct, m_total)

    st.markdown("<div class='card'><b>🧑‍💻 Mening so‘zlarim statistikasi</b><div class='muted'>umumiy natijalar</div></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Testlar", m_attempts)
    c2.metric("Savollar", m_total)
    c3.metric("To‘g‘ri", m_correct)
    c4.metric("Aniqlik", f"{m_pct:.1f}%")

else:
    st.markdown("<div class='card'><b>📚 CSV testlar statistikasi</b><div class='muted'>Test-1, Test-2 ...</div></div>", unsafe_allow_html=True)

    tests = stats_obj.get("csv", {}).get("tests", {})
    if not st.session_state.base_map:
        st.warning("CSV yuklanmagan.")
    else:
        csv_keys_sorted = sorted(st.session_state.base_map.keys())
        total_tests = (len(csv_keys_sorted) + QUESTIONS_PER_TEST - 1) // QUESTIONS_PER_TEST

        rows = []
        for t_id in range(1, total_tests + 1):
            s = tests.get(str(t_id))
            if s and int(s.get("total_q", 0)) > 0:
                tot = int(s.get("total_q", 0))
                cor = int(s.get("correct_q", 0))
                att = int(s.get("attempts", 0))
                rows.append({
                    "Test": f"Test-{t_id}",
                    "Urinish": att,
                    "To‘g‘ri": cor,
                    "Noto‘g‘ri": tot - cor,
                    "Aniqlik": f"{acc_pct(cor, tot):.1f}%"
                })
            else:
                rows.append({"Test": f"Test-{t_id}", "Urinish": 0, "To‘g‘ri": 0, "Noto‘g‘ri": 0, "Aniqlik": "-"})

        st.dataframe(rows, use_container_width=True, hide_index=True)

st.write("")
if st.button("🧹 Statistikani tozalash", use_container_width=True):
    st.session_state.stats_obj = {"manual": {"attempts": 0, "total_q": 0, "correct_q": 0}, "csv": {"tests": {}}}
    save_stats(st.session_state.stats_obj)
    st.success("Tozalandi ✅")
