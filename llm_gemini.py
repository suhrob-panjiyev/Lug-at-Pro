import os
import streamlit as st
import google.generativeai as genai


def _get_api_key():
    return (st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()


def generate_grammar_handout(topic: str, level: str, minutes: int, language: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY topilmadi.")

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

    prompt = f"""
Siz professional English grammar ustozisiz.
Til: {language}
Daraja: {level}
Dars vaqti: {minutes} minut.
Faqat Markdown format.
Mavzu: {topic}
To‘liq handout yarating.
"""

    response = model.generate_content(prompt)

    text = getattr(response, "text", "")
    if not text:
        raise RuntimeError("Gemini javob bermadi.")

    return text.strip()