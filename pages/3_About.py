import streamlit as st

st.set_page_config(page_title="Sayt haqida", page_icon="👤", layout="centered")

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

col_back, col_title = st.columns([1, 5])

with col_back:
    if st.button("⬅ Home", use_container_width=True, key="profile_back_home"):
        st.switch_page("app.py")

with col_title:
    st.title("👤 Sayt haqida")

st.markdown(
    """
**Assalomu alaykum!** Men Suhrob.  
Lug‘at Pro — ingliz tilidagi so‘zlarni samarali yodlash va test qilishni osonlashtirish uchun yaratilgan loyiha. Platforma foydalanuvchilarga lug‘at qo‘shish, darajalar bo‘yicha mashq qilish va natijalarni kuzatish imkonini beradi.

Maqsad — o‘quvchilar va o‘quv markazlari uchun qulay, aqlli va rivojlantiriladigan ta’lim tizimini yaratish.
Yaratuvchi: Suhrob Panjiyev
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
- **Lug‘at yodlashni tezlashtirish**: so‘z qo‘shish, test qilish, statistika orqali muntazam takrorlash.
- **O‘quv markazlar uchun mini platforma**: Student / Teacher / Admin bo‘limlari bilan oddiy, tez va qulay tizim.
- **Teacher AI (tayyor)**: grammar mavzu bo‘yicha professional handout tayyorlaydi (CEFR daraja, vaqt, til bo‘yicha).
- **DOCX / PDF tarqatmalar (tayyor)**: o‘qituvchi bir tugma bilan Word yoki PDF yuklab oladi.
- **Saqlangan materiallar kutubxonasi (tayyor)**: tayyorlangan handout’lar saqlanadi va keyin qayta ishlatiladi (qayta generatsiya shart emas).
- **Admin panel (rivojlanmoqda)**: foydalanuvchilar, sinflar, topshiriqlar va natijalarni nazorat qilish.
- **Kelajakdagi reja**: Telegram bot bilan to‘liq integratsiya, sinfga yuborish, deadline, reyting, XP gamification.

---
### ✅ Hozirgi imkoniyatlar
- Student: **so‘z qo‘shish**, **test**, **statistika**
- Teacher: **AI material generator**, **saqlanganlar**, **PDF/DOCX export**
- Admin: **monitoring va boshqaruv** (bosqichma-bosqich kengaytiriladi)

---
### 🎯 Maqsadli foydalanuvchilar
- Ingliz tili o‘rganuvchilar (studentlar)
- O‘qituvchilar (handout + kutubxona)
- O‘quv markaz administratorlari (nazorat va analitika)
"""
)

st.success("Agar o‘quv markazingizga moslab berish kerak bo‘lsa, bemalol yozing 🙂")
