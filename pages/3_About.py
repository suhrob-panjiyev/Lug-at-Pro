import streamlit as st

st.set_page_config(page_title="Men haqimda", page_icon="👤", layout="centered")

with st.sidebar:
    st.markdown("## 📘 Lug'at Pro")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    if st.button("🎓 Student (Test)", use_container_width=True):
        st.switch_page("pages/1_Student.py")
    if st.button("👨‍🏫 Teacher", use_container_width=True):
        st.switch_page("pages/2_Teacher.py")
    if st.button("👤 Sayt haqida", use_container_width=True):
        st.switch_page("pages/3_About.py")

st.title("👤 Sayt haqida")

st.markdown(
    """
**Assalomu alaykum!** Men Suhrob.  
Lug‘at Pro — ingliz tilidagi so‘zlarni samarali yodlash va test qilishni osonlashtirish uchun yaratilgan loyiha. Platforma foydalanuvchilarga lug‘at qo‘shish, darajalar bo‘yicha mashq qilish va natijalarni kuzatish imkonini beradi.

Maqsad — o‘quvchilar va o‘quv markazlari uchun qulay, aqlli va rivojlantiriladigan ta’lim tizimini yaratish.

### 📌 Kontaktlar
"""
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.link_button("📞 Telefon", "tel:+998886361305", use_container_width=True)

with col2:
    st.link_button("📱 Telegram", "https://t.me/atlet_bro", use_container_width=True)

with col3:
    st.link_button("📸 Instagram", "https://instagram.com/suhrob_panjiyev_", use_container_width=True)

with col4:
    st.link_button("💻 GitHub", "https://github.com/suhrob-panjiyev", use_container_width=True)

st.markdown(
    """
### 🚀 Loyihaning maqsadi
- Lug‘at yodlashni tezlashtirish
- O‘quv markazlar uchun qulay mini platforma
- Keyinchalik: Teacher AI, DOCX/PDF tarqatmalar, admin panel
"""
)

st.success("Agar o‘quv markazingizga moslab berish kerak bo‘lsa, bemalol yozing 🙂")
