import re
from core.user_repo_db import upsert_user as db_upsert_user


def norm_phone(phone: str) -> str:
    phone = re.sub(r"\D+", "", phone or "")
    if phone.startswith("998"):
        phone = "+" + phone
    elif phone.startswith("8"):
        phone = "+998" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+998" + phone
    return phone


def is_valid_uz_phone(phone: str) -> bool:
    phone = norm_phone(phone)
    return bool(re.fullmatch(r"\+998\d{9}", phone))


def upsert_user(first_name: str, last_name: str, phone: str):
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    phone_n = norm_phone(phone)
    return db_upsert_user(first_name, last_name, phone_n)