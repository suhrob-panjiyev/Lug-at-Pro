# 📘 Lug'at Pro

Streamlit asosida yaratilgan inglizcha so‘z yodlash va test qilish uchun mini platforma.

Live Demo:
👉 https://lug-at-pro-suhrob.streamlit.app

---

## 🚀 Loyihaning maqsadi

- Inglizcha so‘zlarni tez va qulay yodlash
- User kiritgan so‘zlar asosida test ishlash
- 5000+ so‘zli CSV datasetdan avtomatik testlar
- O‘quv markazlar uchun MVP platforma

---

## 🧩 Asosiy funksiyalar

### ➕ So‘z qo‘shish
- Real-time qidiruv (4000+ so‘z ichidan tavsiya)
- CSV bazadan avtomatik tarjima topish
- MyMemory API fallback tarjima
- User bazaga saqlash

### 📝 Test tizimi
- Manual (user so‘zlari) testi
- CSV dataset testlari (10 savoldan)
- Variantlar random
- Progress bar
- Natija sahifasi (WOW UI)

### 📊 Statistika
- Manual test statistikasi
- CSV test statistikasi
- To‘g‘ri / noto‘g‘ri / aniqlik foizi
- CSV natijani yuklab olish

---

## 🏗 Texnologiyalar

- Python
- Streamlit
- Pandas
- Requests
- JSON storage
- OpenAI API (Teacher bo‘lim uchun tayyorlangan)

---

## 📂 Loyihaning strukturasi


app.py
pages/
├── 1_Student.py
├── 2_Teacher.py
└── 3_About.py
.streamlit/
requirements.txt
5000_lugat_en_uz.csv



---

## 🔒 Xavfsizlik

API kalitlar GitHub’ga yuklanmaydi.  
Deploy qilingan versiyada kalitlar Streamlit Cloud Secrets orqali saqlanadi.

---

## 🧠 Kelajakdagi reja

- Student bo‘limni 3 faylga ajratish:
  - 1_1_suz_qushish.py
  - 1_2_test.py
  - 1_3_statistika.py
- Teacher AI material generator
- PDF / DOCX export
- Admin panel

---

## 👨‍💻 Muallif

Suhrob Panjiyev  
Telegram: @Suhrobchik_05  
GitHub: https://github.com/suhrob-panjiyev

---

⭐ Agar loyiha yoqsa, star bosishni unutmang.
