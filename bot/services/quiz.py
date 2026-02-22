import csv
import json
import random
from pathlib import Path
from typing import List, Tuple, Set

# =========================
# PATHS (absolute from project root)
# =========================
# bot/services/quiz.py -> parents[2] == project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_CSV = PROJECT_ROOT / "5000_lugat_en_uz.csv"
USER_DATA_FILE = PROJECT_ROOT / "user_words.json"


# =========================
# HELPERS
# =========================
def _strip_bom(s: str) -> str:
    return s.replace("\ufeff", "").strip()


def _norm_key(k: str) -> str:
    return _strip_bom(str(k)).lower()


def _split_translations(uz: str) -> List[str]:
    """"ta'til, bayram" -> ["ta'til", "bayram"]"""
    if not uz:
        return []
    parts = [p.strip() for p in str(uz).split(",")]
    return [p for p in parts if p]


def _pick(d: dict, keys: List[str]) -> str:
    for k in keys:
        if k in d and d[k] is not None:
            val = str(d[k]).strip()
            if val:
                return val
    return ""


def _detect_dialect(sample: str):
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;")
    except Exception:
        return csv.excel


# =========================
# LOADERS
# =========================
def _load_base_words(limit: int = 5000) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    if not BASE_CSV.exists():
        return items

    # utf-8-sig BOM bo'lsa ham tozalab beradi
    with BASE_CSV.open("r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = _detect_dialect(sample)

        reader = csv.DictReader(f, dialect=dialect)
        if not reader.fieldnames:
            return items

        for row in reader:
            if not row:
                continue
            # keylarni normalize qilamiz (BOM, space, case)
            norm = {_norm_key(k): v for k, v in row.items()}

            en = _pick(norm, ["en", "english", "word", "eng"])
            uz = _pick(norm, ["uz", "uzbek", "translation", "tarjima"])

            if en and uz:
                items.append((en, uz))
            if len(items) >= limit:
                break

    return items


def _load_user_words() -> List[Tuple[str, str]]:
    if not USER_DATA_FILE.exists():
        return []

    try:
        data = json.loads(USER_DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    items: List[Tuple[str, str]] = []
    if isinstance(data, dict):
        for v in data.values():
            try:
                en = str(v.get("en", "")).strip()
                uz = str(v.get("uz", "")).strip()
            except Exception:
                continue
            if en and uz:
                items.append((en, uz))

    return items


# =========================
# PUBLIC API
# =========================
def build_questions(n: int) -> List[Tuple[str, str]]:
    """CSV doim asosiy manba. user_words bo'lsa qo'shiladi."""
    base = _load_base_words()
    user = _load_user_words()

    pool = base + user
    # duplicatesni olib tashlaymiz
    pool = list({(en, uz) for en, uz in pool})

    random.shuffle(pool)
    return pool[: max(0, n)]


def build_options(correct_uz: str, pool_all_uz: List[str], k: int = 4) -> List[str]:
    """Correct tarjima ichida vergul bo'lsa, variantlardan bittasini correct qilamiz."""
    translations = _split_translations(correct_uz)
    correct = random.choice(translations) if translations else str(correct_uz).strip()

    synonyms = set(translations)
    wrong = list({u for u in pool_all_uz if u and (u not in synonyms) and (u != correct)})
    random.shuffle(wrong)

    opts = [correct] + wrong[: max(0, k - 1)]
    random.shuffle(opts)
    return opts


def normalize_correct_for_check(original_uz: str) -> Set[str]:
    parts = _split_translations(original_uz)
    return set(parts) if parts else {str(original_uz).strip()}


def get_all_uz_pool() -> List[str]:
    """Return a big pool of all Uzbek translations from CSV + user_words."""
    base = _load_base_words(limit=500000)
    user = _load_user_words()
    pool = [uz for _, uz in (base + user) if uz]
    # unique while preserving order
    seen = set()
    out = []
    for u in pool:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def build_fixed_quiz(n: int, seed: int | None = None, k_options: int = 4) -> List[dict]:
    """
    Build a fixed quiz payload (same questions/options for everyone).
    Returns list of dicts: {en, uz, options}
    """
    rnd = random.Random(seed)

    # build question set
    base = _load_base_words()
    user = _load_user_words()
    pool_pairs = list({(en, uz) for en, uz in (base + user)})
    rnd.shuffle(pool_pairs)
    questions = pool_pairs[: max(0, n)]

    # options pool from all uz (bigger, better)
    all_uz = [uz for _, uz in pool_pairs if uz]

    def _options(correct_uz: str) -> List[str]:
        translations = _split_translations(correct_uz)
        correct = rnd.choice(translations) if translations else str(correct_uz).strip()
        synonyms = set(translations)
        wrong = list({u for u in all_uz if u and (u not in synonyms) and (u != correct)})
        rnd.shuffle(wrong)
        opts = [correct] + wrong[: max(0, k_options - 1)]
        rnd.shuffle(opts)
        return opts

    payload = []
    for en, uz in questions:
        payload.append({"en": en, "uz": uz, "options": _options(uz)})
    return payload
