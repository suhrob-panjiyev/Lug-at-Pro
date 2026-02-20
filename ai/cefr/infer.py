# ai/cefr/infer.py
from __future__ import annotations
from pathlib import Path
import re
import joblib

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "cefr_model.joblib"

def clean_word(w: str) -> str:
    w = (w or "").strip().lower()
    w = re.sub(r"\s+", " ", w)
    w = re.sub(r"[^a-z0-9'\- ]", "", w)
    return w.strip()

def load_model(path: str | None = None):
    p = Path(path) if path else MODEL_PATH
    return joblib.load(p)

def predict_level(model, word: str) -> str:
    w = clean_word(word)
    if not w:
        return "-"
    return model.predict([w])[0]