import re

def norm_en(s: str) -> str:
    return " ".join(str(s).strip().lower().split())

def norm_uz(s: str) -> str:
    return " ".join(str(s).strip().lower().split())

def clean_header(h: str) -> str:
    return str(h).replace("\ufeff", "").strip().lower()

def clean_word_basic(w: str) -> str:
    w = (w or "").strip().lower()
    w = re.sub(r"\s+", " ", w)
    w = re.sub(r"[^a-z0-9'\- ]", "", w)
    return w.strip()