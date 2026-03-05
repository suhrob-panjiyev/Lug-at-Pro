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
tab_users, tab_detail = st.tabs(["📋 Foydalanuvchilar", "👤 Tanlangan foydalanuvchi"])

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

st.markdown("</div>", unsafe_allow_html=True)