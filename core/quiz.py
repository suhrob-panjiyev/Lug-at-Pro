import random
from typing import Optional, List, Dict

from core.text import norm_uz


def unique_all_uz(map_: dict) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in map_.values():
        for u in (v.get("uz_list") or []):
            nu = norm_uz(u)
            if u.strip() and nu not in seen:
                seen.add(nu)
                out.append(u)
    return out


def build_question_from_map(map_: dict, en_key: str) -> Dict:
    item = map_[en_key]
    en = item["en"]
    uz_list = item.get("uz_list") or []
    correct = random.choice(uz_list) if uz_list else "(tarjima yo‘q)"

    pool = unique_all_uz(map_)
    pool = [u for u in pool if norm_uz(u) != norm_uz(correct)]
    random.shuffle(pool)
    wrongs = pool[:3]

    fillers = ["velosiped", "samolyot", "poyezd", "telefon", "kitob", "daraxt", "stol", "qalam"]
    for f in fillers:
        if len(wrongs) >= 3:
            break
        if norm_uz(f) != norm_uz(correct) and all(norm_uz(f) != norm_uz(w) for w in wrongs):
            wrongs.append(f)

    options = [correct] + wrongs[:3]
    random.shuffle(options)
    return {"en": en, "correct": correct, "options": options}


def start_quiz_state(ss, mode: str, keys: List[str], csv_test_id: Optional[int] = None):
    ss.quiz_mode = mode
    ss.quiz_keys = keys
    ss.quiz_index = 0
    ss.quiz_score = 0
    ss.quiz_answers = []
    ss.quiz_page = "run"
    ss.csv_test_id = csv_test_id
    ss.result_saved = False


def reset_quiz_state(ss):
    ss.quiz_page = "menu"
    ss.quiz_mode = None
    ss.quiz_keys = []
    ss.quiz_index = 0
    ss.quiz_score = 0
    ss.quiz_answers = []
    ss.csv_test_id = None
    ss.current_q = None
    ss.current_q_id = None
    ss.q_choice = None
    ss.pop("q_choice_widget", None)