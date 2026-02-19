import streamlit as st
from streamlit_searchbox import st_searchbox

from pages.student_core import (
    render_sidebar, ensure_state,
    inject_student_css, render_hero, render_top_nav,
    norm_en, suggestions, translate_mymemory, is_weird_translation,
    save_user_words
)

st.set_page_config(page_title="Student — So‘z qo‘shish", page_icon="➕", layout="wide")
render_sidebar(active="student")
ensure_state()
inject_student_css()
render_hero()
render_top_nav(active="add", page_key="add")



st.markdown("### ➕ So‘z qo‘shish")

# ---- state init ----
if "en_input" not in st.session_state:
    st.session_state.en_input = ""
if "last_translations" not in st.session_state:
    st.session_state.last_translations = []

# ---------------------------
# 1) SINGLE INPUT: live searchbox
# ---------------------------
def search_fn(q: str):
    q = (q or "").strip()
    if not q:
        return []

    # bazadan tavsiyalar
    sug = suggestions(q, st.session_state.english_list_csv, limit=16)

    # ✅ user typed so‘z ham birinchi bo‘lsin (car ham chiqadi)
    if q and all(q.lower() != s.lower() for s in sug):
        sug = [q] + sug
    else:
        # agar sug ichida bo‘lsa ham, q ni 1-chi qilish (car birinchi)
        # (case-insensitive)
        q_low = q.lower()
        sug_sorted = [q]
        for s in sug:
            if s.lower() != q_low:
                sug_sorted.append(s)
        sug = sug_sorted

    # dedupe
    seen = set()
    out = []
    for w in sug:
        lw = w.lower()
        if lw not in seen:
            seen.add(lw)
            out.append(w)

    return out[:16]


picked = st_searchbox(
    search_fn,
    key="en_live",
    placeholder="car, app, apple ...",
    label="English so‘zni yozing"
)

# picked bo‘lsa: user tanladi yoki Enter bosdi (q ro‘yxatda 1-chi bo‘lgani uchun q qaytadi)
en_word = (picked or "").strip()

# statega yozib qo‘yamiz (keyingi bo‘limlar uchun)
if en_word:
    st.session_state.en_input = en_word

en_key = norm_en(en_word)

st.divider()

# ---------------------------
# CSV’da bor bo‘lsa
# ---------------------------
if en_key and en_key in st.session_state.base_map:
    item = st.session_state.base_map[en_key]
    st.success("Topildi ✅ (CSV bazadan)")

    existing = item.get("uz_list") or []
    selected = st.multiselect(
        "Tarjimalarni tanlang:",
        existing,
        default=existing[:1] if existing else []
    )

    if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(len(selected) == 0)):
        st.session_state.user_map[en_key] = {"en": item["en"], "uz_list": selected}
        save_user_words(st.session_state.user_map)
        st.success("Saqlandi ✅")

# ---------------------------
# CSV’da yo‘q bo‘lsa
# ---------------------------
else:
    st.info("Bu so‘z CSV bazada yo‘q. Istasangiz avtomatik tarjima qilib saqlaysiz.")

    a, b, c = st.columns([1.2, 1.2, 1.2])
    with a:
        do_translate = st.button("🔄 Avto tarjima", use_container_width=True, disabled=not en_word)
    with b:
        only_best = st.toggle("⭐ Faqat 1 ta tarjima", value=True)
    with c:
        manual = st.toggle("✍️ Qo‘lda kiritaman", value=False)

    if do_translate and en_word:
        with st.spinner("Tarjima qilinyapti..."):
            try:
                tr = translate_mymemory(en_word)
                tr = [x for x in tr if not is_weird_translation(x)]
                if only_best and tr:
                    tr = tr[:1]
                st.session_state.last_translations = tr
            except Exception as e:
                st.session_state.last_translations = []
                st.error(f"Tarjima xatosi: {e}")

    if manual:
        uz_text = st.text_area("Tarjima (har qatorda bittadan)", placeholder="misol")
        selected = [x.strip() for x in uz_text.splitlines() if x.strip()]
    else:
        default_pick = st.session_state.last_translations[:1] if st.session_state.last_translations else []
        selected = st.multiselect(
            "Topilgan tarjima(lar):",
            st.session_state.last_translations,
            default=default_pick
        )

    if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(not en_word or len(selected) == 0)):
        st.session_state.user_map[en_key] = {"en": en_word, "uz_list": selected}
        save_user_words(st.session_state.user_map)
        st.success("Saqlandi ✅")

# ---------------------------
# Footer
# ---------------------------
k1, k2 = st.columns(2)
k1.metric("User so‘zlari", len(st.session_state.user_map))
k2.metric("CSV so‘zlari", len(st.session_state.base_map))
