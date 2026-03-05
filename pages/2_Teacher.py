import streamlit as st
from pages.student_core import require_login, render_sidebar, inject_student_css

require_login()
st.set_page_config(page_title="Teacher", page_icon="👨‍🏫", layout="wide")

render_sidebar(active="teacher")
inject_student_css()

st.markdown(
    """
<style>
.teacher-hero{
  padding: 18px 20px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  margin-bottom: 16px;
}
.teacher-hero h1{
  margin: 0;
  font-size: 44px;
  line-height: 1.1;
}
.teacher-hero p{
  margin: 8px 0 0 0;
  opacity: 0.85;
  font-size: 16px;
}
.teacher-grid{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 10px;
}
@media (max-width: 900px){
  .teacher-grid{ grid-template-columns: 1fr; }
}
.teacher-card{
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  padding: 16px 16px 14px 16px;
}
.teacher-card:hover{
  border-color: rgba(255,255,255,0.16);
  background: rgba(255,255,255,0.04);
}
.teacher-card .top{
  display:flex;
  align-items:center;
  gap:10px;
  margin-bottom: 6px;
}
.teacher-card .icon{
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size: 20px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
}
.teacher-card h3{
  margin:0;
  font-size: 22px;
}
.teacher-card .desc{
  margin: 6px 0 10px 0;
  opacity: 0.85;
}
.teacher-pill{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  opacity: 0.9;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.04);
  margin-right: 6px;
  margin-bottom: 8px;
}
.teacher-list{
  margin: 8px 0 10px 18px;
  opacity: 0.9;
}
.teacher-list li{ margin: 4px 0; }
.teacher-footer{
  margin-top: 12px;
  opacity: 0.75;
  font-size: 13px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="teacher-hero">
  <h1>👨‍🏫 Teacher bo‘limi</h1>
  <p>Qaysi bo‘limga o‘tmoqchisiz? Kerakli bo‘limni tanlang — qolganini tizim o‘zi tartiblaydi.</p>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)

with c1:
    st.markdown(
        """
<div class="teacher-card">
  <div class="top">
    <div class="icon">📄</div>
    <div>
      <h3>Materiallar tayyorlash</h3>
      <div class="desc">Grammatika material/handout tayyorlash, saqlash va yuklab olish.</div>
    </div>
  </div>

  <span class="teacher-pill">⚡ Tez tayyorlash</span>
  <span class="teacher-pill">🗂️ Saqlash</span>
  <span class="teacher-pill">⬇️ Yuklab olish</span>

  <ul class="teacher-list">
    <li>Mavzu bo‘yicha tayyor material generatsiya</li>
    <li>Qisqa va tushunarli tuzilma</li>
    <li>O‘qituvchiga qulay format</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("➡️ Materiallar sahifasiga o‘tish", use_container_width=True, key="go_handout"):
        st.switch_page("pages/2_Teacher_Handout.py")

with c2:
    st.markdown(
        """
<div class="teacher-card">
  <div class="top">
    <div class="icon">🤖</div>
    <div>
      <h3>Bot orqali topshiriq</h3>
      <div class="desc">Test yaratish va Telegram guruhga bot orqali yuborish.</div>
    </div>
  </div>

  <span class="teacher-pill">🧪 Test yaratish</span>
  <span class="teacher-pill">📢 Guruhga yuborish</span>
  <span class="teacher-pill">📈 Monitoring</span>

  <ul class="teacher-list">
    <li>Sinf tanlab assignment yaratish</li>
    <li>Deadline va active holat boshqaruvi</li>
    <li>Sinflar / urinishlar statistikasi</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("➡️ Bot topshiriq sahifasiga o‘tish", use_container_width=True, key="go_bot"):
        st.switch_page("pages/2_Teacher_Bot.py")

st.markdown(
    """
<div class="teacher-footer">
  💡 Maslahat: “Bot orqali topshiriq” bo‘limida sinfni tanlab yuborishdan oldin bot ishga tushganini tekshirib oling.
</div>
""",
    unsafe_allow_html=True,
)