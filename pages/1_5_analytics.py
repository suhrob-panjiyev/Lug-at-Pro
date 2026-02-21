import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav,
    acc_pct
)

st.set_page_config(page_title="Student — Grafiklar", page_icon="📈", layout="wide")
render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav(active="stats", page_key="analytics")

st.markdown("### 📈 Grafiklar (Analytics)")

# --- Back button ---
c_back, c_hint = st.columns([1, 3])
with c_back:
    if st.button("⬅️ Statistika", use_container_width=True):
        st.switch_page("pages/1_3_statistika.py")
with c_hint:
    st.caption("Bu sahifa: qaysi joyda sust ketayotganingizni tez ko‘rsatadi.")

stats_obj = st.session_state.stats_obj

# ---------------------------
# Helpers: history -> df
# ---------------------------
def to_df(hist: list, kind: str):
    if not hist:
        return pd.DataFrame(columns=["ts", "pct", "correct", "total", "kind", "test_id"])
    df = pd.DataFrame(hist)
    df["kind"] = kind
    df["ts"] = pd.to_datetime(df.get("ts"), errors="coerce")
    if "test_id" not in df.columns:
        df["test_id"] = None
    df = df.dropna(subset=["ts"]).sort_values("ts")
    return df

manual_df = to_df(stats_obj.get("manual", {}).get("history", []), "Manual")
csv_df = to_df(stats_obj.get("csv", {}).get("history", []), "CSV")

# ✅ Test-None ni yo'qotamiz (csv test_id None bo'lsa)
if not csv_df.empty:
    csv_df = csv_df[csv_df["test_id"].notna()].copy()
    csv_df["test_id"] = pd.to_numeric(csv_df["test_id"], errors="coerce")
    csv_df = csv_df.dropna(subset=["test_id"]).copy()
    csv_df["test_id"] = csv_df["test_id"].astype(int)

# ---------------------------
# Base metrics
# ---------------------------
m = stats_obj.get("manual", {})
m_attempts = int(m.get("attempts", 0))
m_total = int(m.get("total_q", 0))
m_correct = int(m.get("correct_q", 0))
m_pct = acc_pct(m_correct, m_total)

tests = stats_obj.get("csv", {}).get("tests", {})
csv_total = sum(int(v.get("total_q", 0)) for v in tests.values())
csv_correct = sum(int(v.get("correct_q", 0)) for v in tests.values())
csv_attempts = sum(int(v.get("attempts", 0)) for v in tests.values())
csv_pct = acc_pct(csv_correct, csv_total)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Manual aniqlik", f"{m_pct:.1f}%")
k2.metric("CSV aniqlik", f"{csv_pct:.1f}%")
k3.metric("Manual urinish", m_attempts)
k4.metric("CSV urinish", csv_attempts)

st.divider()

# ==========================================================
# 1) DONUT: Manual vs CSV accuracy
# ==========================================================
st.markdown("#### 1) Umumiy aniqlik — donut ko‘rinish")

colA, colB = st.columns([1.2, 1])

with colA:
    # Donut chart (2 rings)
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.set_title("Aniqlik (%) — Manual vs CSV")

    values = [m_pct, csv_pct]
    labels = ["Manual", "CSV"]

    # pie -> donut
    wedges, _ = ax.pie(
        values,
        labels=labels,
        startangle=90,
        wedgeprops=dict(width=0.35)
    )

    # Center text
    ax.text(0, 0.05, f"{(m_pct+csv_pct)/2:.1f}%", ha="center", va="center", fontsize=16, fontweight="bold")
    ax.text(0, -0.18, "o‘rtacha", ha="center", va="center", fontsize=10, alpha=0.8)

    ax.axis("equal")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

with colB:
    st.markdown(
        """
        **Bu nimani beradi?**  
        - Manual va CSV natijani ko‘z bilan tez solishtirasiz.  
        - O‘rtacha % markazda turadi.
        """
    )

st.divider()

# ==========================================================
# 2) SPARKLINE TREND: last N attempts
# ==========================================================
st.markdown("#### 2) So‘nggi urinishlar trendi — sparkline (zamonaviy, kichik)")

N = st.slider("Oxirgi nechta urinish?", 10, 120, 40, step=10)

df_all = pd.concat([manual_df, csv_df], ignore_index=True)
df_all = df_all.dropna(subset=["ts"]).sort_values("ts").tail(N)

if df_all.empty:
    st.info("Trend ko‘rish uchun history yo‘q. Bir nechta test ishlang 🙂")
else:
    # Sparkline style: 2 ta kichik grafik yonma-yon
    sp1, sp2 = st.columns(2)

    def spark(df_kind: pd.DataFrame, title: str):
        fig, ax = plt.subplots(figsize=(6.2, 1.8))
        y = df_kind["pct"].to_list()
        x = list(range(1, len(y) + 1))
        ax.plot(x, y, linewidth=2.2, marker="o", markersize=3.5)
        ax.fill_between(x, y, alpha=0.15)
        ax.set_title(title)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.25)

        # minimal axes
        ax.set_xticks([])
        ax.set_ylabel("%")

        if y:
            ax.text(x[-1], y[-1], f"  {y[-1]:.0f}%", va="center", fontsize=10)

        fig.tight_layout()
        return fig

    with sp1:
        d = df_all[df_all["kind"] == "Manual"].copy()
        st.pyplot(spark(d, "Manual — oxirgi urinishlar"), use_container_width=True)

    with sp2:
        d = df_all[df_all["kind"] == "CSV"].copy()
        st.pyplot(spark(d, "CSV — oxirgi urinishlar"), use_container_width=True)

st.divider()

# ==========================================================
# 3) HEATMAP: CSV tests accuracy map
# ==========================================================
st.markdown("#### 3) CSV testlar heatmap — qaysi testlar qiyin?")

rows = []
for test_id, v in tests.items():
    tot = int(v.get("total_q", 0))
    cor = int(v.get("correct_q", 0))
    att = int(v.get("attempts", 0))
    if tot > 0 and str(test_id).isdigit():
        rows.append({"test_id": int(test_id), "pct": acc_pct(cor, tot), "att": att, "tot": tot})

d = pd.DataFrame(rows).sort_values("test_id")
d["test_id"] = pd.to_numeric(d["test_id"], errors="coerce")
d = d.dropna(subset=["test_id"]).copy()
d["test_id"] = d["test_id"].astype(int)
if d.empty:
    st.info("CSV testlar hali ishlanmagan.")
else:
    # heatmap grid: 10 ustunli panel ko‘rinish
    cols = 10
    max_id = int(d["test_id"].max())
    size = max_id

    # 1..max_id bo‘yicha array tayyorlaymiz
    acc_arr = np.full(size, np.nan, dtype=float)
    att_arr = np.zeros(size, dtype=int)

    for _, r in d.iterrows():
        try:
            tid = int(r["test_id"])
        except Exception:
            continue
        if tid < 1 or tid > size:
            continue

        acc_arr[tid - 1] = float(r["pct"])
        att_arr[tid - 1] = int(r["att"])

    # reshape
    rows_n = int(np.ceil(size / cols))
    padded = rows_n * cols - size
    if padded:
        acc_arr = np.concatenate([acc_arr, np.full(padded, np.nan)])
        att_arr = np.concatenate([att_arr, np.zeros(padded, dtype=int)])

    acc_grid = acc_arr.reshape(rows_n, cols)
    att_grid = att_arr.reshape(rows_n, cols)

    fig, ax = plt.subplots(figsize=(8.0, 3.4))
    im = ax.imshow(acc_grid, aspect="auto")

    ax.set_title("CSV testlar aniqligi heatmap (0–100%)")
    ax.set_xlabel("Test bloklari")
    ax.set_ylabel("Qatorlar")

    # cell text: % va urinish
    for i in range(rows_n):
        for j in range(cols):
            val = acc_grid[i, j]
            if np.isnan(val):
                continue
            t_id = i * cols + j + 1
            ax.text(j, i, f"{t_id}\n{val:.0f}%", ha="center", va="center", fontsize=8)

    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

    # foydali jadval (top-10 qiyin)
    d2 = d.sort_values("pct", ascending=True).head(10).copy()
    d2["Test"] = d2["test_id"].apply(lambda x: f"Test-{x}")
    d2["Aniqlik"] = d2["pct"].map(lambda x: f"{x:.1f}%")
    d2 = d2[["Test", "Aniqlik", "att", "tot"]].rename(columns={"att": "Urinish", "tot": "Savollar"})
    st.dataframe(d2, use_container_width=True, hide_index=True)

st.divider()

# ==========================================================
# 4) SCATTER: Attempts vs Accuracy (CSV)
# ==========================================================
st.markdown("#### 4) Urinish vs Aniqlik — qayerda ko‘p urinyapsiz, natija qanday?")

if d.empty:
    st.info("Scatter uchun CSV testlar yetarli emas.")
else:
    # ✅ ustun nomini himoyalaymiz
    if "att" not in d.columns:
        # ba'zan 'attempts' deb chiqib qolishi mumkin
        if "attempts" in d.columns:
            d["att"] = d["attempts"]
        else:
            d["att"] = 0  # fallback

    if "pct" not in d.columns:
        st.warning("Aniqlik ma'lumoti yo‘q (pct).")
    else:
        fig, ax = plt.subplots(figsize=(7.0, 3.0))
        ax.scatter(d["att"], d["pct"], s=70, alpha=0.85)
        ax.set_title("CSV: Urinish soni vs Aniqlik (%)")
        ax.set_xlabel("Urinish (attempts)")
        ax.set_ylabel("Aniqlik (%)")
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.25)

        # eng qiyin 5 ta nuqtani label qilamiz
        if "test_id" in d.columns:
            hard = d.sort_values("pct", ascending=True).head(5)
            for _, r in hard.iterrows():
                try:
                    tid = int(r["test_id"])
                except Exception:
                    tid = "?"
                ax.text(float(r["att"]) + 0.05, float(r["pct"]) + 0.8, f"T{tid}", fontsize=9)

        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)