import random
import streamlit as st

st.set_page_config(page_title="Admin kirish — Lug'at Pro", page_icon="🛡️", layout="wide")

# --- Init state ---
st.session_state.setdefault("admin_authed", False)

# Captcha state
st.session_state.setdefault("adm_a", random.randint(1, 9))
st.session_state.setdefault("adm_b", random.randint(1, 9))
st.session_state.setdefault("adm_op", random.choice(["+", "-"]))


def regen_captcha():
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    op = random.choice(["+", "-"])

    # ✅ minus bo‘lsa manfiy bo‘lib qolmasin
    if op == "-" and b > a:
        a, b = b, a

    st.session_state.adm_a = a
    st.session_state.adm_b = b
    st.session_state.adm_op = op


def captcha_answer(a: int, b: int, op: str) -> int:
    return a + b if op == "+" else a - b


# ---------------------------
# CSS
# ---------------------------
st.markdown(
    """
<style>
  .page {
    max-width: 900px;
    margin: 0 auto;
  }
  .hero{
    padding: 18px 18px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.10);
    background: linear-gradient(135deg, rgba(80,120,255,0.20), rgba(0,0,0,0));
    margin-bottom: 14px;
  }
  .title{
    font-size: 34px;
    font-weight: 900;
    line-height: 1.05;
  }
  .muted{opacity:.82}
  .box{
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.03);
  }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="page">', unsafe_allow_html=True)

st.markdown(
    """
<div class="hero">
  <div class="title">🛡️ Admin kirish</div>
  <div class="muted" style="margin-top:6px;">
    Admin panelga kirish uchun login + parol va oddiy captcha kerak.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---- UI ----
st.markdown('<div class="box">', unsafe_allow_html=True)

# captcha values
a, b, op = st.session_state.adm_a, st.session_state.adm_b, st.session_state.adm_op

# Refresh tugma (formdan tashqarida — qulayroq)
r1, r2 = st.columns([5, 1.3])
with r2:
    if st.button("🔄 Yangilash", use_container_width=True):
        regen_captcha()
        st.rerun()

with st.form("admin_login_form", clear_on_submit=False):
    admin_name = st.text_input("Login", value="", placeholder="Admin")
    pwd = st.text_input("Parol", type="password", placeholder="Admin parol...")

    st.caption("Captcha (oddiy misol):")
    cap = st.text_input(f"{a} {op} {b} = ?", placeholder="Javob")

    ok = st.form_submit_button("✅ Kirish", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- Logic ----
if ok:
    admin_pass = st.secrets.get("ADMIN_PASSWORD", "").strip()
    if not admin_pass:
        st.error("ADMIN_PASSWORD topilmadi. (.streamlit/secrets.toml ni tekshiring)")
        regen_captcha()
        st.stop()

    correct = captcha_answer(a, b, op)

    # ✅ hammasi bitta xabar bilan tekshiriladi (xavfsizroq)
    name_ok = (admin_name or "").strip().lower() == "admin"
    pwd_ok = (pwd or "").strip() == admin_pass

    try:
        cap_int = int((cap or "").strip())
        cap_ok = (cap_int == correct)
    except Exception:
        cap_ok = False

    if not (name_ok and pwd_ok and cap_ok):
        st.error("Kirish ma’lumotlari noto‘g‘ri.")
        regen_captcha()
        st.stop()

    st.session_state.admin_authed = True
    st.success("Admin panelga kirdingiz ✅")
    st.switch_page("pages/5_Admin.py")