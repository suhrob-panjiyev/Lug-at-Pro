import json
from datetime import datetime
from pathlib import Path

def _default_stats():
    return {
        "manual": {"attempts": 0, "total_q": 0, "correct_q": 0, "history": []},
        "csv": {"tests": {}, "history": []},
        "level": {"by_level": {}, "history": []},
    }

def _ts():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def acc_pct(correct: int, total: int) -> float:
    return (correct / total * 100.0) if total else 0.0

def sanitize_stats(stats_obj: dict) -> dict:
    # csv.tests ichida "None" yoki digit bo'lmagan keylarni olib tashlash
    try:
        tests = stats_obj.get("csv", {}).get("tests", {})
        bad = [k for k in list(tests.keys()) if not str(k).isdigit()]
        for k in bad:
            tests.pop(k, None)
    except Exception:
        pass
    return stats_obj

def load_stats(stats_file: Path):
    if not stats_file.exists():
        return _default_stats()
    try:
        obj = json.loads(stats_file.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            return _default_stats()

        obj.setdefault("manual", {"attempts": 0, "total_q": 0, "correct_q": 0, "history": []})
        obj["manual"].setdefault("history", [])

        obj.setdefault("csv", {"tests": {}, "history": []})
        obj["csv"].setdefault("tests", {})
        obj["csv"].setdefault("history", [])

        obj.setdefault("level", {"by_level": {}, "history": []})
        obj["level"].setdefault("by_level", {})
        obj["level"].setdefault("history", [])

        return sanitize_stats(obj)
    except Exception:
        return _default_stats()

def save_stats(stats_file: Path, stats_obj: dict):
    stats_obj = sanitize_stats(stats_obj)
    stats_file.write_text(json.dumps(stats_obj, ensure_ascii=False, indent=2), encoding="utf-8")

def record_manual_result(stats_obj: dict, correct: int, total: int):
    m = stats_obj.setdefault("manual", {"attempts": 0, "total_q": 0, "correct_q": 0, "history": []})
    m.setdefault("history", [])
    m["attempts"] = int(m.get("attempts", 0)) + 1
    m["total_q"] = int(m.get("total_q", 0)) + int(total)
    m["correct_q"] = int(m.get("correct_q", 0)) + int(correct)
    m["history"].append({"ts": _ts(), "correct": int(correct), "total": int(total), "pct": acc_pct(correct, total)})

def record_csv_result(stats_obj: dict, test_id: int, correct: int, total: int):
    c = stats_obj.setdefault("csv", {"tests": {}, "history": []})
    c.setdefault("tests", {})
    c.setdefault("history", [])

    test_id = int(test_id)
    t = c["tests"].get(str(test_id), {"attempts": 0, "total_q": 0, "correct_q": 0})
    t["attempts"] = int(t.get("attempts", 0)) + 1
    t["total_q"] = int(t.get("total_q", 0)) + int(total)
    t["correct_q"] = int(t.get("correct_q", 0)) + int(correct)
    c["tests"][str(test_id)] = t

    c["history"].append({"ts": _ts(), "test_id": test_id, "correct": int(correct), "total": int(total), "pct": acc_pct(correct, total)})

def record_level_result(stats_obj: dict, level: str, correct: int, total: int):
    level = (level or "-").strip().upper()
    lv = stats_obj.setdefault("level", {"by_level": {}, "history": []})
    lv.setdefault("by_level", {})
    lv.setdefault("history", [])

    cur = lv["by_level"].get(level, {"attempts": 0, "total_q": 0, "correct_q": 0})
    cur["attempts"] = int(cur.get("attempts", 0)) + 1
    cur["total_q"] = int(cur.get("total_q", 0)) + int(total)
    cur["correct_q"] = int(cur.get("correct_q", 0)) + int(correct)
    lv["by_level"][level] = cur

    lv["history"].append({"ts": _ts(), "level": level, "correct": int(correct), "total": int(total), "pct": acc_pct(correct, total)})