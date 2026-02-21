from typing import List
from core.text import norm_en


def suggestions(query: str, english_list: List[str], limit: int = 16):
    q = norm_en(query)
    if not q:
        return []

    starts = [w for w in english_list if w.lower().startswith(q)]
    if len(starts) >= limit:
        return starts[:limit]

    contains = [w for w in english_list if q in w.lower() and w not in starts]
    return (starts + contains)[:limit]