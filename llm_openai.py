import os

def _get_openai_key() -> str:
    key = ""
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass
    if not key:
        key = os.getenv("OPENAI_API_KEY", "")
    return key.strip()

def generate_grammar_handout(topic: str, level: str, minutes: int, language: str) -> str:
    from openai import OpenAI

    api_key = _get_openai_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY topilmadi (secrets.toml yoki env).")

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are an experienced English grammar teacher.
Return a PROFESSIONAL handout in Markdown.
Language: {language}
Level: {level}
Duration: {minutes} minutes
Topic: {topic}

Structure:
1) Title
2) Lesson goals (3-5)
3) Form table (affirmative/negative/question)
4) Usage rules
5) Examples (8-10)
6) Common mistakes (5-6) + corrections
7) Practice: blanks (6-8), MCQ (5-6), transform (5-6), translation EN<->UZ (4-6), speaking (4-5)
8) TEACHER KEY (answers) at the end

Keep it concise (1–2 pages).
"""

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
    )
    return (resp.output_text or "").strip()
