import json
from pathlib import Path
import streamlit as st

from core.text import norm_en


def load_user_words(user_data_file: Path) -> dict:
    if not user_data_file.exists():
        return {}

    try:
        raw = json.loads(user_data_file.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return {}

        data = {}
        for item in raw:
            if not isinstance(item, dict):
                continue

            en = str(item.get("en", "")).strip()
            uz_list = item.get("uz_list") or []
            uz_list = [str(x).strip() for x in uz_list if str(x).strip()]

            if not en or not uz_list:
                continue

            data[norm_en(en)] = {"en": en, "uz_list": uz_list}

        return data

    except Exception:
        return {}


def save_user_words(user_data_file: Path, user_map: dict) -> None:
    arr = [{"en": v["en"], "uz_list": v["uz_list"]} for v in user_map.values()]
    user_data_file.write_text(
        json.dumps(arr, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


@st.cache_data(show_spinner=False)
def english_list_from_map(map_: dict):
    return sorted({v["en"] for v in map_.values()}, key=lambda x: x.lower())