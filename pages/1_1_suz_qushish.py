import streamlit as st
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
render_top_nav()

st.markdown("### ➕ So‘z qo‘shish")

typed = st.text_input(
    "English so‘zni yozing",
    key=f"en_input_widget_{st.session_state.en_nonce}",
    value=st.session_state.en_input,
    placeholder="car, example, apple ..."
)

if typed != st.session_state.en_input:
    st.session_state.en_input = typed

en_word = (st.session_state.en_input or "").strip()
en_key = norm_en(en_word)

sug = suggestions(en_word, st.session_state.english_list_csv, limit=16)

if en_word and sug:
    pick = st.selectbox(
        "Tavsiya tanlang (ixtiyoriy):",
        options=["—"] + sug,
        index=0,
        help="Yozishni boshlang → tavsiyalar chiqadi → bittasini tanlang."
    )
    if pick != "—":
        st.session_state.en_input = pick
        st.session_state.en_nonce += 1
        st.rerun()

if en_word:
    st.markdown("<div class='sug-title'><b>Tavsiyalar:</b></div>", unsafe_allow_html=True)
    if not sug:
        st.caption("Hech narsa topilmadi. Yozuvni tekshiring.")
    else:
        cols = st.columns(8)
        for i, w in enumerate(sug):
            with cols[i % 8]:
                if st.button(w, key=f"sug_{w}_{i}", use_container_width=True):
                    st.session_state.en_input = w
                    st.session_state.en_nonce += 1
                    st.rerun()

st.divider()

if en_key and en_key in st.session_state.base_map:
    item = st.session_state.base_map[en_key]
    st.success("Topildi ✅ (CSV bazadan)")

    existing = item.get("uz_list") or []
    selected = st.multiselect("Tarjimalarni tanlang:", existing, default=existing[:1] if existing else [])

    if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(len(selected) == 0)):
        st.session_state.user_map[en_key] = {"en": item["en"], "uz_list": selected}
        save_user_words(st.session_state.user_map)
        st.success("Saqlandi ✅")
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
        selected = st.multiselect("Topilgan tarjima(lar):", st.session_state.last_translations, default=default_pick)

    if st.button("💾 Saqlash", type="primary", use_container_width=True, disabled=(not en_word or len(selected) == 0)):
        st.session_state.user_map[en_key] = {"en": en_word, "uz_list": selected}
        save_user_words(st.session_state.user_map)
        st.success("Saqlandi ✅")

k1, k2 = st.columns(2)
k1.metric("User so‘zlari", len(st.session_state.user_map))
k2.metric("CSV so‘zlari", len(st.session_state.base_map))
