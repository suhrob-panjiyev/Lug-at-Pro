import csv
from pathlib import Path
import streamlit as st

from core.text import clean_header, norm_en, norm_uz


def detect_columns(fieldnames):
    if not fieldnames:
        return None, None

    cleaned = [clean_header(f) for f in fieldnames]

    en_candidates = ["en", "english", "word", "eng"]
    uz_candidates = ["uz", "uzbek", "translation", "meaning", "tr", "uzb"]

    en_col = None
    uz_col = None

    for c in en_candidates:
        if c in cleaned:
            en_col = fieldnames[cleaned.index(c)]
            break

    for c in uz_candidates:
        if c in cleaned:
            uz_col = fieldnames[cleaned.index(c)]
            break

    return en_col, uz_col


@st.cache_data(show_spinner=False)
def load_base_csv(path_str: str):
    path = Path(path_str)
    data = {}
    meta = {"ok": False, "rows": 0, "en_col": None, "uz_col": None, "error": None}

    if not path.exists():
        meta["error"] = f"CSV topilmadi: {path.resolve()}"
        return data, meta

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            en_col, uz_col = detect_columns(reader.fieldnames)

            meta["en_col"] = en_col
            meta["uz_col"] = uz_col

            if not en_col or not uz_col:
                meta["error"] = f"Ustun topilmadi. Fieldnames: {reader.fieldnames}"
                return data, meta

            for row in reader:
                meta["rows"] += 1
                en = (row.get(en_col) or "").strip()
                uz = (row.get(uz_col) or "").strip()
                if not en or not uz:
                    continue

                k = norm_en(en)
                data.setdefault(k, {"en": en, "uz_list": []})

                if all(norm_uz(uz) != norm_uz(x) for x in data[k]["uz_list"]):
                    data[k]["uz_list"].append(uz)

        meta["ok"] = True
        return data, meta

    except Exception as e:
        meta["error"] = str(e)
        return data, meta