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

# ✅ MUST be at the top (Streamlit talabi)
st.set_page_config(page_title="Admin — Lug'at Pro", page_icon="🛡️", layout="wide")

# ✅ Guard: admin login shart
if not st.session_state.get("admin_authed", False):
    st.switch_page("pages/5_Admin_Login.py")
    st.stop()

# ---------------------------
# CSS (Admin UI)
# ---------------------------
st.markdown(
    """
<style>
  .page {
    max-width: 1200px;
    margin: 0 auto;
  }
  .topbar {
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap: 16px;
    margin-bottom: 12px;
  }
  .title {
    font-size: 34px;
    font-weight: 900;
    line-height: 1.05;
    margin: 0;
  }
  .subtitle { opacity: .82; margin-top: 6px; }

  .card{
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.03);
  }
  .section-title{
    font-size: 18px;
    font-weight: 800;
    margin: 4px 0 10px 0;
  }
  .muted{ opacity: .78; }
  .kpi-label { opacity: .70; font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="page">', unsafe_allow_html=True)

# ---------------------------
# TOP BAR
# ---------------------------
topL, topR = st.columns([6, 1.4])
with topL:
    st.markdown(
        """
        <div class="topbar">
          <div>
            <div class="title">🛡️ Admin panel</div>
            <div class="subtitle">Foydalanuvchilar, natijalar va umumiy ko‘rsatkichlar.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with topR:
    if st.button("🚪 Chiqish (logout)", use_container_width=True):
        st.session_state.admin_authed = False
        st.switch_page("app.py")

st.write("")

# ---------------------------
# FILTER PANEL (Card)
# ---------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">🔎 Qidirish va tartiblash</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns([2.2, 1.4, 1.2])
with c1:
    q = st.text_input(
        "Qidirish (ism / familiya / telefon)",
        value="",
        placeholder="Masalan: +998..., Suhrob ...",
    )
with c2:
    sort = st.selectbox(
        "Tartiblash",
        ["last_login_desc", "avg_pct_desc", "attempts_desc", "words_desc"],
        format_func=lambda x: {
            "last_login_desc": "Oxirgi kirganlar (yangilari avval)",
            "avg_pct_desc": "Natija foizi (yuqorisi avval)",
            "attempts_desc": "Test ishlaganlar (ko‘pi avval)",
            "words_desc": "So‘zlari ko‘p (ko‘pi avval)",
        }[x],
    )
with c3:
    limit = st.selectbox("Nechtasini ko‘rsatamiz?", [25, 50, 100, 200], index=1)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# LOAD USERS
# ---------------------------
rows = list_users_with_metrics(q=q, sort=sort)[: int(limit)]
if not rows:
    st.info("Hech qanday foydalanuvchi topilmadi.")
    st.stop()

df = pd.DataFrame(rows)
df["full_name"] = (df["first_name"].fillna("") + " " + df["last_name"].fillna("")).str.strip()
df["avg_pct"] = df["avg_pct"].astype(float)

# ---------------------------
# GLOBAL KPIs (Card)
# ---------------------------
st.write("")
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">📌 Umumiy ko‘rsatkichlar</div>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Foydalanuvchilar", len(df))
k2.metric("O‘rtacha natija", f"{df['avg_pct'].mean():.1f}%")
k3.metric("Umumiy testlar", int(df["attempts_count"].sum()))
k4.metric("Umumiy so‘zlar", int(df["words_count"].sum()))

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# MAIN TABS
# ---------------------------
st.write("")
tab_users, tab_detail, tab_bot = st.tabs(["📋 Foydalanuvchilar", "👤 Tanlangan foydalanuvchi", "🤖 Bot monitoring"])

with tab_users:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 Foydalanuvchilar ro‘yxati</div>', unsafe_allow_html=True)
    st.caption("Pastdagi ro‘yxatdan userni tanlab, keyingi tabda batafsil ko‘rasiz.")

    show_cols = ["id", "full_name", "phone", "words_count", "attempts_count", "avg_pct", "last_login_at"]
    st.dataframe(
        df[show_cols].rename(
            columns={
                "id": "ID",
                "full_name": "Ism Familiya",
                "phone": "Telefon",
                "words_count": "So‘zlar soni",
                "attempts_count": "Testlar soni",
                "avg_pct": "O‘rtacha natija (%)",
                "last_login_at": "Oxirgi kirgan vaqti",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    pick = st.selectbox(
        "👤 Foydalanuvchini tanlang (batafsil ko‘rish uchun)",
        options=df["id"].tolist(),
        format_func=lambda uid: f"{int(uid)} — "
        f"{df.loc[df['id']==uid, 'full_name'].values[0]} "
        f"({df.loc[df['id']==uid, 'phone'].values[0]})",
    )

with tab_detail:
    # pick default (agar user hali tanlamagan bo‘lsa)
    if "pick_admin_user" not in st.session_state:
        st.session_state.pick_admin_user = int(df["id"].iloc[0])

    # agar tab_users’da tanlansa, saqlab qo‘yamiz
    try:
        st.session_state.pick_admin_user = int(pick)
    except Exception:
        pass

    uid = int(st.session_state.pick_admin_user)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👤 Foydalanuvchi batafsil</div>', unsafe_allow_html=True)

    one = df[df["id"] == uid].iloc[0]
    st.markdown(
        f"**{one['full_name']}**  \n"
        f"Telefon: **{one['phone']}**  \n"
        f"Oxirgi kirgan: **{one['last_login_at']}**",
    )

    summary = get_user_attempts_summary(uid)
    overall = summary["overall"]
    by_mode = summary["by_mode"]

    st.write("")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Testlar soni", int(overall["attempts"]))
    d2.metric("Savollar soni", int(overall["total_q"]))
    d3.metric("To‘g‘ri javoblar", int(overall["correct_q"]))
    d4.metric("O‘rtacha natija", f"{float(overall['avg_pct']):.1f}%")

    st.write("")
    st.caption("🔎 Qaysi turdagi testda natija qanday?")

    mcols = st.columns(3)
    pretty = {"manual": "Mening so‘zlarim", "csv": "CSV testlar", "level": "Level testi"}
    for i, mode in enumerate(["manual", "csv", "level"]):
        m = by_mode.get(mode, {"attempts": 0, "avg_pct": 0, "total_q": 0, "correct_q": 0})
        with mcols[i]:
            st.markdown(f"**{pretty[mode]}**")
            st.metric("Testlar", int(m["attempts"]))
            st.metric("O‘rtacha natija", f"{float(m['avg_pct']):.1f}%")

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🕒 Oxirgi testlar</div>', unsafe_allow_html=True)
    st.caption("Eng oxirgi 100 ta urinish (bo‘lsa).")

    attempts = get_user_attempts(uid, limit=100)
    adf = pd.DataFrame(attempts)

    if adf.empty:
        st.info("Bu foydalanuvchi hali test ishlamagan.")
    else:
        show = ["ts", "mode", "test_id", "level", "score", "total", "pct"]
        mode_map = {"manual": "Mening so‘zlarim", "csv": "CSV", "level": "Level"}
        adf["mode"] = adf["mode"].map(lambda x: mode_map.get(x, x))

        st.dataframe(
            adf[show].rename(
                columns={
                    "ts": "Vaqt",
                    "mode": "Test turi",
                    "test_id": "CSV test raqami",
                    "level": "Level",
                    "score": "To‘g‘ri",
                    "total": "Jami savol",
                    "pct": "Natija (%)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with tab_bot:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 Telegram Bot — Monitoring</div>', unsafe_allow_html=True)
    st.caption("Bu bo‘lim bot ishlatayotgan classroom.db dan o‘qiydi. Web (app.db) ga tegmaydi — xavfsiz.")

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
        dfc.rename(
            columns={
                "id": "ID",
                "name": "Nomi",
                "group_id": "Group ID",
                "teacher_id": "Teacher ID",
                "created_at": "Yaratilgan",
                "members_count": "A’zolar",
                "assignments_count": "Topshiriqlar",
                "attempts_count": "Urinishlar",
                "xp_sum": "Jami XP",
            }
        ),
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
    # ✅ 2) Assignment yaratish form (Web → Bot)
    # ============================================================
    st.write("")
    st.markdown("### ➕ Assignment yaratish (Web → Bot)")

    with st.form("create_assignment_form", clear_on_submit=False):
        n_questions = st.number_input(
            "Savollar soni (n_questions)", min_value=1, max_value=50, value=10, step=1
        )
        deadline_hhmm = st.text_input(
            "Deadline (HH:MM) ixtiyoriy",
            value="23:59",
            help="Masalan: 18:30 yoki 23:59. Bo‘sh qoldirsangiz deadline bo‘lmaydi.",
        )
        deactivate_prev = st.checkbox(
            "Oldingi assignment(lar)ni o‘chirib, faqat yangisini Active qil", value=True
        )

        submitted = st.form_submit_button("✅ Create assignment")

        if submitted:
            dh = deadline_hhmm.strip()
            if dh == "":
                dh = None

            # Minimal validatsiya
            if dh is not None:
                ok = (len(dh) == 5 and dh[2] == ":" and dh[:2].isdigit() and dh[3:].isdigit())
                if not ok:
                    st.error("Deadline formati noto‘g‘ri. Masalan: 18:30")
                    st.stop()

            aid = create_assignment_web(int(class_id), int(n_questions), dh, deactivate_prev=deactivate_prev)
            st.success(f"✅ Assignment yaratildi! ID={aid}")
            st.rerun()

    # ---------------------------
    # Assignments list
    # ---------------------------
    dfa = list_assignments(int(class_id))

    st.write("")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧪 Assignments</div>', unsafe_allow_html=True)

    if dfa.empty:
        st.info("Bu sinfda hali assignment yo‘q.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    show_a = dfa[
        ["id", "n_questions", "deadline_hhmm", "deadline_at", "is_active", "created_at", "attempts_count", "avg_pct"]
    ].copy()
    show_a["avg_pct"] = show_a["avg_pct"].fillna(0).map(lambda x: f"{float(x):.1f}%")

    st.dataframe(
        show_a.rename(
            columns={
                "id": "ID",
                "n_questions": "Savollar",
                "deadline_hhmm": "Deadline (HH:MM)",
                "deadline_at": "Deadline (ISO)",
                "is_active": "Active",
                "created_at": "Yaratilgan",
                "attempts_count": "Attempts",
                "avg_pct": "Avg %",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    assignment_id = st.selectbox(
        "Assignment tanlang (attemptlarni ko‘rish uchun)",
        options=dfa["id"].tolist(),
        format_func=lambda aid: (
            f"{int(aid)} — {dfa.loc[dfa['id']==aid,'created_at'].values[0]} "
            f"(Q={int(dfa.loc[dfa['id']==aid,'n_questions'].values[0])})"
        ),
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ============================================================
    # ✅ 3) Assignment Active/Deactive qilish tugmalari
    # ============================================================
    st.write("")
    st.markdown("### ⚙️ Assignment holati (Active/Deactive)")

    assignment_id2 = st.selectbox(
        "Assignment tanlang (holatini o‘zgartirish uchun)",
        options=dfa["id"].tolist(),
        format_func=lambda aid: f"{int(aid)} — active={int(dfa.loc[dfa['id']==aid,'is_active'].values[0])}",
        key="assignment_status_picker",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🟢 Activate", use_container_width=True):
            set_assignment_active(int(assignment_id2), int(class_id), True)
            st.success("Activated ✅")
            st.rerun()

    with c2:
        if st.button("⚪ Deactivate", use_container_width=True):
            set_assignment_active(int(assignment_id2), int(class_id), False)
            st.success("Deactivated ✅")
            st.rerun()

    # ---------------------------
    # Attempts + Leaderboard
    # ---------------------------
    st.write("")
    dfatt = list_attempts(int(assignment_id))

    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📄 Attempts (tanlangan assignment)</div>', unsafe_allow_html=True)

        if dfatt.empty:
            st.info("Hali hech kim ishlamagan.")
        else:
            df_show = dfatt.copy()
            df_show["pct"] = df_show["pct"].map(lambda x: f"{float(x):.1f}%")
            df_show["is_late"] = df_show["is_late"].map(lambda x: "✅" if int(x) == 1 else "—")

            cols = ["user_id", "full_name", "score", "total", "pct", "finished_at", "is_late"]

            st.dataframe(
                df_show[cols].rename(
                    columns={
                        "user_id": "User ID",
                        "full_name": "Ism",
                        "score": "Score",
                        "total": "Total",
                        "pct": "%",
                        "finished_at": "Tugadi",
                        "is_late": "Late",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🏆 Leaderboard</div>', unsafe_allow_html=True)

        st.caption("📅 Daily top (bugun)")
        d1 = daily_top(int(class_id), 10)
        if d1.empty:
            st.write("—")
        else:
            st.dataframe(
                d1.rename(columns={"user_id": "User ID", "full_name": "Ism", "xp": "XP"}),
                hide_index=True,
                use_container_width=True,
            )

        st.write("")
        st.caption("🗓 Weekly top (shu hafta)")
        d2 = weekly_top(int(class_id), 10)
        if d2.empty:
            st.write("—")
        else:
            st.dataframe(
                d2.rename(columns={"user_id": "User ID", "full_name": "Ism", "xp": "XP"}),
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)