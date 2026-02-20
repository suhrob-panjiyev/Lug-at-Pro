# auth.py
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

USERS_FILE = Path("users.json")


def norm_phone(phone: str) -> str:
    """+998... formatga yaqinlashtiramiz (faqat raqam va +)."""
    phone = (phone or "").strip()
    phone = phone.replace(" ", "").replace("-", "")
    # faqat + va raqam qolsin
    phone = re.sub(r"[^\d+]", "", phone)

    # agar + bo'lmasa, raqam bo'lsa qo'shamiz (MVP)
    if phone and not phone.startswith("+"):
        if phone.startswith("998"):
            phone = "+" + phone
        elif phone.startswith("0"):
            # 0xxxxxxxxx -> +998xxxxxxxxx (taxmin)
            phone = "+998" + phone.lstrip("0")
    return phone


def is_valid_uz_phone(phone: str) -> bool:
    p = norm_phone(phone)
    # +998 bilan 12-13 uzunlik (masalan +998901234567 -> 13)
    return bool(re.fullmatch(r"\+998\d{9}", p))


def load_users() -> Dict[str, Any]:
    if not USERS_FILE.exists():
        return {"users": {}}
    try:
        obj = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            return {"users": {}}
        obj.setdefault("users", {})
        if not isinstance(obj["users"], dict):
            obj["users"] = {}
        return obj
    except Exception:
        return {"users": {}}


def save_users(obj: Dict[str, Any]) -> None:
    USERS_FILE.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_user(first_name: str, last_name: str, phone: str) -> Dict[str, Any]:
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    phone_n = norm_phone(phone)

    users_obj = load_users()
    users = users_obj["users"]

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    u = users.get(phone_n)

    if not u:
        u = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone_n,
            "created_at": now,
            "last_login_at": now,
        }
    else:
        # yangilab qo'yamiz (MVP)
        u["first_name"] = first_name or u.get("first_name", "")
        u["last_name"] = last_name or u.get("last_name", "")
        u["last_login_at"] = now

    users[phone_n] = u
    save_users(users_obj)
    return u


def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    phone_n = norm_phone(phone)
    users_obj = load_users()
    return users_obj.get("users", {}).get(phone_n)