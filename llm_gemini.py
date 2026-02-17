import os
import google.generativeai as genai

def _get_api_key() -> str:
    """
    API key ni avval Streamlit secrets’dan, bo‘lmasa env’dan oladi.
    Streamlit bo‘lmagan holatda ham ishlashi uchun try/except qildik.
    """
    api_key = ""
    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""

    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")

    return api_key.strip()

def generate_grammar_handout(topic: str, level: str, minutes: int, language: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY topilmadi. secrets.toml yoki env ga qo'ying.")

    genai.configure(api_key=api_key)

    # Sizda mavjud va MVP uchun ideal:
    MODEL_PRIMARY = "models/gemini-2.0-flash"
    MODEL_FALLBACK = "models/gemini-2.5-pro"

    system_prompt = f"""
Siz professional English grammar ustozisiz.
Natija: PROFESSIONAL handout (tarqatma) bo'lsin.
Til: {language}
Daraja: {level}
Dars vaqti: {minutes} minut
Faqat GRAMMAR.
Output faqat Markdown formatida.
"""

    user_prompt = f"""
Mavzu: {topic}

Struktura:
1) Title
2) Lesson goals (3-5)
3) Form (affirmative/negative/question) jadval bilan
4) Usage rules
5) Examples (kamida 10 ta)
6) Common mistakes (kamida 6 ta + to‘g‘ri varianti)
7) Practice:
   - Fill in the blanks (8 ta)
   - Multiple choice (6 ta)
   - Transform sentences (6 ta)
   - Translation EN<->UZ (6 ta)
   - Speaking prompts (5 ta)
8) TEACHER KEY (javoblar) — oxirida ajratib yozing
"""

    text_in = system_prompt + "\n" + user_prompt

    # Avval tez/arzon model, bo'lmasa fallback
    try:
        model = genai.GenerativeModel(MODEL_PRIMARY)
        response = model.generate_content(text_in)
    except Exception:
        model = genai.GenerativeModel(MODEL_FALLBACK)
        response = model.generate_content(text_in)

    return (response.text or "").strip()
