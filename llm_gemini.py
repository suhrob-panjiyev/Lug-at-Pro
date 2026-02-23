import os
import streamlit as st
from google import genai


def _get_api_key():
    return (st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()


def generate_grammar_handout(topic: str, level: str, minutes: int, language: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY topilmadi.")

    client = genai.Client(api_key=api_key)

    model_id = "gemini-1.5-flash"   # eng stabil model

    prompt = f"""
Siz professional English grammar ustozisiz.
Natija PROFESSIONAL handout bo'lsin.
Til: {language}
Daraja: {level}
Dars vaqti: {minutes} minut
Faqat GRAMMAR.
Output faqat Markdown.

Mavzu: {topic}

Struktura:
1) Title
2) Lesson goals
3) Form table
4) Usage rules
5) 10 examples
6) 6 common mistakes
7) Practice
8) Teacher key
"""

    response = client.models.generate_content(
        model=model_id,
        contents=prompt
    )

    text = getattr(response, "text", "")
    if not text:
        raise RuntimeError("Gemini javob bermadi.")

    return text.strip()