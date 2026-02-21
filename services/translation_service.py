import requests
import streamlit as st


@st.cache_data(show_spinner=False)
def translate_mymemory(en_text: str):
    en_text = en_text.strip()
    if not en_text:
        return []

    url = "https://api.mymemory.translated.net/get"
    params = {"q": en_text, "langpair": "en|uz"}

    r = requests.get(url, params=params, timeout=12)
    r.raise_for_status()
    data = r.json()

    candidates = []

    main = (data.get("responseData") or {}).get("translatedText", "")
    if main:
        candidates.append(main)

    for m in (data.get("matches") or []):
        t = (m.get("translation") or "").strip()
        if t:
            candidates.append(t)

    cleaned, seen = [], set()
    for c in candidates:
        c2 = " ".join(c.strip().split())
        key = c2.lower()
        if c2 and key not in seen:
            seen.add(key)
            cleaned.append(c2)

    return cleaned[:10]


def is_weird_translation(t: str) -> bool:
    s = t.strip().lower()
    if not s:
        return True
    if len(s) > 35:
        return True
    if any(x in s for x in ["3d", "histogram", "diagram", "grafik"]):
        return True
    if "-" in s and len(s) > 18:
        return True
    return False