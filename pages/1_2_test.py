import streamlit as st
import random
import pandas as pd
from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav,
    QUESTIONS_PER_TEST, norm_uz,
    start_quiz, reset_quiz_to_menu, build_question_from_map,
    acc_pct, record_manual_result, record_csv_result, record_level_result,
    save_stats, require_login
)

require_login()

st.set_page_config(page_title="Student — Test", page_icon="📝", layout="wide")
render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav(active="test", page_key="test")

st.markdown("### 📝 Test")

# ---------------------------
# MENU
# ---------------------------
if st.session_state.quiz_page == "menu":
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            "<div class='card'><b>🧑‍💻 Mening so‘zlarim</b><div class='muted'>Siz saqlagan so‘zlardan test.</div></div>",
            unsafe_allow_html=True
        )
        if st.button("Boshlash ▶️", type="primary", use_container_width=True):
            if len(st.session_state.user_map) < 2:
                st.error("Avval kamida 2 ta so‘z saqlang.")
            else:
                keys = list(st.session_state.user_map.keys())
                random.shuffle(keys)
                keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                start_quiz("manual", keys)
                st.rerun()

    with c2:
        st.markdown(
            "<div class='card'><b>📚 CSV testlar</b><div class='muted'>Bazadan bo‘lingan testlar.</div></div>",
            unsafe_allow_html=True
        )
        if st.button("Testlar ro‘yxati ➜", type="primary", use_container_width=True):
            if len(st.session_state.base_map) < QUESTIONS_PER_TEST:
                st.error("CSV’da yetarli so‘z yo‘q.")
            else:
                st.session_state.quiz_page = "csv_list"
                st.rerun()

    st.caption("Har bir test: 10 ta savol.")

# ---------------------------
# CSV TEST LIST
# ---------------------------
elif st.session_state.quiz_page == "csv_list":
    topA, topB, topC = st.columns([1.2, 1.2, 2.0])

    with topA:
        if st.button("⬅️ Test menyu", use_container_width=True):
            reset_quiz_to_menu()
            st.rerun()

    with topB:
        if st.button("🧑‍💻 Mening so‘zlarim testi", use_container_width=True, type="primary"):
            if len(st.session_state.user_map) < 2:
                st.error("Avval kamida 2 ta so‘z saqlang.")
            else:
                keys = list(st.session_state.user_map.keys())
                random.shuffle(keys)
                keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                start_quiz("manual", keys)
                st.rerun()

    with topC:
        q_test = st.text_input("🔎 Test raqami (masalan: 12)", value="", placeholder="...")

    csv_keys_sorted = sorted(st.session_state.base_map.keys())
    total_tests = (len(csv_keys_sorted) + QUESTIONS_PER_TEST - 1) // QUESTIONS_PER_TEST
    tests_stats = st.session_state.stats_obj["csv"]["tests"]

    show_ids = list(range(1, total_tests + 1))
    if q_test.strip().isdigit():
        t = int(q_test.strip())
        show_ids = [t] if 1 <= t <= total_tests else []

    st.write("")
    for t_id in show_ids:
        stat = tests_stats.get(str(t_id))
        if stat and stat.get("total_q", 0) > 0:
            c = int(stat.get("correct_q", 0))
            tot = int(stat.get("total_q", 0))
            w = tot - c
            p = acc_pct(c, tot)
            label = f"Test-{t_id} • ✅ {c} • ❌ {w} • {p:.0f}%"
        else:
            label = f"Test-{t_id} • (hali ishlanmagan)"

        rowA, rowB = st.columns([3, 1])
        with rowA:
            st.write(label)
        with rowB:
            if st.button("▶️", key=f"start_test_{t_id}", use_container_width=True):
                start_idx = (t_id - 1) * QUESTIONS_PER_TEST
                chunk = csv_keys_sorted[start_idx:start_idx + QUESTIONS_PER_TEST]
                start_quiz("csv", chunk, csv_test_id=t_id)
                st.rerun()

# ---------------------------
# RUN QUIZ
# ---------------------------
elif st.session_state.quiz_page == "run":
    mode = st.session_state.quiz_mode

    if mode == "manual":
        source_map = st.session_state.user_map
    else:
        # csv ham, level ham base_map’dan foydalanadi
        source_map = st.session_state.base_map

    keys = st.session_state.quiz_keys
    idx = st.session_state.quiz_index
    total_q = len(keys)

    if idx >= total_q:
        st.session_state.quiz_page = "result"
        st.rerun()

    q_id = f"{mode}:{st.session_state.get('csv_test_id')}:{idx}"

    # savolni faqat bir marta build qilish
    if st.session_state.current_q_id != q_id or st.session_state.current_q is None:
        st.session_state.current_q_id = q_id
        current_key = keys[idx]
        st.session_state.current_q = build_question_from_map(source_map, current_key)

    q = st.session_state.current_q

    if mode == "manual":
        title = "🧑‍💻 Mening so‘zlarim"
    elif mode == "level":
        title = "📚 Level testi"
    else:
        title = f"📚 CSV Test-{st.session_state.csv_test_id}"

    st.info(title + f" • {idx+1}/{total_q}")
    st.markdown(f"## **{q['en']}**")

    # har savol uchun radio key unik
    radio_key = f"q_choice_{q_id}"
    st.radio(
        "Tarjimani tanlang:",
        q["options"],
        index=None,
        key=radio_key
    )

    choice = st.session_state.get(radio_key)

    a, b, c = st.columns([1.2, 1, 1.2])

    with a:
        if st.button("✅ Yuborish", type="primary", use_container_width=True, disabled=(choice is None)):
            ok = (norm_uz(choice) == norm_uz(q["correct"]))

            if ok:
                st.session_state.quiz_score += 1
                st.success("To‘g‘ri ✅")
            else:
                st.error(f"Noto‘g‘ri ❌  To‘g‘risi: **{q['correct']}**")

            st.session_state.quiz_answers.append({
                "en": q["en"],
                "your": choice,
                "correct": q["correct"],
                "ok": ok
            })

            # shu savolning tanlovini tozalaymiz
            st.session_state.pop(radio_key, None)

            st.session_state.quiz_index += 1
            st.session_state.current_q = None
            st.session_state.current_q_id = None

            if st.session_state.quiz_index >= total_q:
                st.session_state.quiz_page = "result"

            st.rerun()

    with b:
        st.metric("Score", f"{st.session_state.quiz_score}/{total_q}")

    with c:
        if st.button("🛑 To‘xtatish", use_container_width=True):
            reset_quiz_to_menu()
            st.rerun()

    st.progress(idx / total_q)

# ---------------------------
# RESULT
# ---------------------------
elif st.session_state.quiz_page == "result":
    mode = st.session_state.quiz_mode
    total_q = len(st.session_state.quiz_keys)
    score = st.session_state.quiz_score
    wrong = total_q - score
    p = acc_pct(score, total_q)

    # natijani 1 marta saqlash
    if "result_saved" not in st.session_state:
        st.session_state.result_saved = False
# ======================================================


    if not st.session_state.result_saved:

        if mode == "manual":    
            record_manual_result(
                st.session_state.stats_obj,
                score,
                total_q
            )

        elif mode == "level":
            lv = st.session_state.get("current_level", "-")
            record_level_result(
                st.session_state.stats_obj,
                lv,
                score,
                total_q
            )

        elif mode == "csv":
            t_id = st.session_state.get("csv_test_id")
            if t_id is not None:
                record_csv_result(
                    st.session_state.stats_obj,
                    int(t_id),
                    score,
                    total_q
                )

                save_stats(st.session_state.stats_obj)
                st.session_state.result_saved = True

    if mode == "manual":
        mode_title = "🧑‍💻 Mening so‘zlarim"
    elif mode == "level":
        mode_title = "📚 Level testi"
    else:
        mode_title = f"📚 CSV Test-{st.session_state.csv_test_id}"

    if p >= 90:
        label = "🔥 A’lo!"
    elif p >= 75:
        label = "✅ Juda yaxshi!"
    elif p >= 50:
        label = "🙂 Yaxshi"
    else:
        label = "💪 Qayta urinib ko‘ring"

    st.markdown(
        f"""
        <div class="hero">
          <div class="pill">{mode_title}</div>
          <div class="pill">Savollar: <b>{total_q}</b></div>
          <div class="pill">To‘g‘ri: <b>{score}</b></div>
          <div class="pill">Noto‘g‘ri: <b>{wrong}</b></div>
          <div style="margin-top:10px" class="big">Natija: {score}/{total_q} • {p:.1f}%</div>
          <div class="muted" style="margin-top:6px">{label}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")
    st.progress(min(max(p / 100.0, 0.0), 1.0))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Score", f"{score}/{total_q}")
    m2.metric("Aniqlik", f"{p:.1f}%")
    m3.metric("To‘g‘ri", score)
    m4.metric("Noto‘g‘ri", wrong)

    st.divider()

    answers = st.session_state.quiz_answers or []
    if answers:
        df = pd.DataFrame(answers)

        df["status"] = df["ok"].apply(lambda x: "✅" if x else "❌")
        df["en_show"] = df["en"].astype(str)
        df["your_show"] = df["your"].astype(str)
        df["correct_show"] = df["correct"].astype(str)

        # faqat bitta toggle
        show_table = st.toggle("📊 Jadval", value=True)

        # CSV export (hammasi)
        csv_bytes = df[["en_show", "your_show", "correct_show", "status"]].rename(
            columns={
                "en_show": "English",
                "your_show": "Siz tanlagan",
                "correct_show": "To‘g‘ri javob",
                "status": "Holat"
            }
        ).to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "⬇️ Natijani CSV qilib olish",
            data=csv_bytes,
            file_name="lugat_test_natija.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.write("")

        if show_table:
            st.dataframe(
                df[["status", "en_show", "your_show", "correct_show"]].rename(
                    columns={
                        "status": "",
                        "en_show": "English",
                        "your_show": "Siz tanlagan",
                        "correct_show": "To‘g‘ri javob"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            for _, r in df.iterrows():
                ok = bool(r["ok"])
                icon = "✅" if ok else "❌"
                hint = ""
                if not ok:
                    hint = f"<div class='muted'>To‘g‘risi: <b>{r['correct_show']}</b></div>"

                st.markdown(
                    f"""
                    <div class="qa-card">
                      <div style="display:flex; gap:10px; align-items:center;">
                        <div style="font-size:20px">{icon}</div>
                        <div>
                          <div><b>English:</b> {r["en_show"]}</div>
                          <div class="muted"><b>Siz tanlagan:</b> {r["your_show"]}</div>
                          {hint}
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.divider()

    a, b, c = st.columns(3)

    with a:
        if st.button("⬅️ Menyu", type="primary", use_container_width=True):
            st.session_state.result_saved = False
            reset_quiz_to_menu()
            st.rerun()

    with b:
        if st.button("🔁 Qayta", use_container_width=True):
            st.session_state.result_saved = False

            if mode == "manual":
                if len(st.session_state.user_map) < 2:
                    st.error("User so‘zlari kam.")
                else:
                    keys = list(st.session_state.user_map.keys())
                    random.shuffle(keys)
                    keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                    start_quiz("manual", keys)
                    st.rerun()

            elif mode == "level":
                keys = list(st.session_state.quiz_keys or [])
                if len(keys) < 2:
                    st.error("Level so‘zlari kam.")
                else:
                    random.shuffle(keys)
                    keys = keys[:QUESTIONS_PER_TEST] if len(keys) >= QUESTIONS_PER_TEST else keys
                    start_quiz("level", keys)
                    st.rerun()

            else:  # csv
                t_id = st.session_state.csv_test_id
                if not t_id:
                    st.error("CSV test ID topilmadi.")
                    reset_quiz_to_menu()
                    st.rerun()

                csv_keys_sorted = sorted(st.session_state.base_map.keys())
                start_idx = (int(t_id) - 1) * QUESTIONS_PER_TEST
                chunk = csv_keys_sorted[start_idx:start_idx + QUESTIONS_PER_TEST]
                start_quiz("csv", chunk, csv_test_id=int(t_id))
                st.rerun()

    with c:
        # faqat CSV mode uchun "Testlar" ko'rsatsin
        if mode == "csv":
            if st.button("📚 Testlar", use_container_width=True):
                st.session_state.result_saved = False
                st.session_state.quiz_page = "csv_list"
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answers = []
                st.session_state.current_q = None
                st.session_state.current_q_id = None
                st.session_state.q_choice = None
                st.session_state.pop("q_choice_widget", None)
                st.rerun()
        else:
            st.empty()