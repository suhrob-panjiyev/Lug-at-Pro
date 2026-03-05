from __future__ import annotations

from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile,
)

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from bot.storage.db import get_conn
from bot.services.quiz import normalize_correct_for_check
from bot.services.classroom import (
    ensure_member,
    save_attempt,
    get_group_id_by_class,
    get_assignment_questions,
    is_assignment_late,
)

router = Router()
TZ = ZoneInfo("Asia/Samarkand")

# MVP state (RAM). Keyin DB/Redis ga o'tkazamiz.
QUIZ = {}  # user_id -> state


def get_assignment_row(assignment_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, class_id, n_questions, is_active FROM assignments WHERE id=?",
        (int(assignment_id),),
    )
    row = cur.fetchone()
    conn.close()
    return row


def get_class_name(class_id: int) -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM classes WHERE id=?", (class_id,))
    row = cur.fetchone()
    conn.close()
    return (row[0] if row and row[0] else "Class")


@router.message(F.text.startswith("/start"))
async def start_router(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Assalomu alaykum! 👋")
        return

    payload = parts[1]

    # =========================
    # homework start: hw_<assignment_id>
    # =========================
    if payload.startswith("hw_"):
        import bot.storage.db as _db
        print("📌 student db =", _db.DB_PATH)

        try:
            assignment_id = int(payload.split("_")[1])
        except Exception:
            await message.answer("❌ Link xato: assignment_id topilmadi.")
            return

        row = get_assignment_row(assignment_id)

        # ✅ DEBUG: row nima qaytaryapti?
        print("🧾 assignment row =", row, "| type =", type(row))

        if not row:
            await message.answer("Bu topshiriq topilmadi (DBda yo‘q).")
            return

        # sqlite Row bo'lsa dictga o'xshaydi, tuple bo'lsa index bilan
        is_active = row["is_active"] if hasattr(row, "keys") else row[3]
        class_id = row["class_id"] if hasattr(row, "keys") else row[1]
        n_q = row["n_questions"] if hasattr(row, "keys") else row[2]

        # ✅ DEBUG: ajratib olingan qiymatlar
        print("🔎 parsed:", {"assignment_id": assignment_id, "class_id": class_id, "n_q": n_q, "is_active": is_active})

        if int(is_active) != 1:
            await message.answer("Bu topshiriq hozir aktiv emas (is_active=0).")
            return

        fixed = get_assignment_questions(assignment_id)
        if not fixed:
            await message.answer(
                "Bu topshiriq uchun test tayyorlanmagan. O‘qituvchi /give_hw ni qayta bersin."
            )
            return
        
        # fixed list of dict bo'lishi shart
        if not isinstance(fixed, list) or (fixed and not isinstance(fixed[0], dict)):
            await message.answer("Test formatida xatolik bor (questions_json). O‘qituvchi topshiriqni qayta yaratsin.")
            return

        # fixed payload: [{"en":..., "uz":..., "options":[...]}]
        questions = [(q["en"], q["uz"], q.get("options") or []) for q in fixed]

        # ✅ Robust: user join link ishlatmagan bo‘lsa ham members’ga yozib qo‘yamiz
        ensure_member(class_id, message.from_user.id, message.from_user.full_name)

        # ✅ late flag
        late = is_assignment_late(assignment_id)

        QUIZ[message.from_user.id] = {
            "assignment_id": assignment_id,
            "class_id": class_id,
            "i": 0,
            "score": 0,
            "questions": questions,
            "answers": [],
            "is_late": 1 if late else 0,
        }

        if late:
            await message.answer(
                "⏰ Deadline o‘tib ketgan, lekin siz topshiriqni *late* sifatida topshirasiz."
            )

        await message.answer("📝 Topshiriq boshlandi! Javobni tanlang.")
        await send_question(message)
        return

    # =========================
    # join_<class_id>
    # =========================
    if payload.startswith("join_"):
        class_id = int(payload.split("_")[1])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO members (class_id, user_id, full_name) VALUES (?, ?, ?)",
            (class_id, message.from_user.id, message.from_user.full_name),
        )
        conn.commit()
        conn.close()
        await message.answer("🎉 Siz sinfga qo‘shildingiz!")
        return


async def send_question(message: Message):
    st = QUIZ.get(message.from_user.id)
    if not st:
        return

    i = st["i"]
    qs = st["questions"]

    # =========================
    # FINISH
    # =========================
    if i >= len(qs):
        total = len(qs)
        score = st["score"]
        pct = round((score / total) * 100, 1) if total else 0.0

        answers_json = json.dumps(st.get("answers", []), ensure_ascii=False)
        is_late = int(st.get("is_late", 0))

        save_attempt(
            st["assignment_id"],
            st["class_id"],
            message.from_user.id,
            message.from_user.full_name,
            score,
            total,
            pct,
            is_late=is_late,
            answers_json=answers_json,
        )

        # XP hisoblash
        xp = score * 10
        if pct == 100:
            xp += 20

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO xp_log (class_id, user_id, full_name, xp) VALUES (?, ?, ?, ?)",
            (st["class_id"], message.from_user.id, message.from_user.full_name, xp),
        )
        conn.commit()
        conn.close()

        # Guruhga natija
        group_id = get_group_id_by_class(st["class_id"])
        if group_id:
            late_txt = " ⏰ LATE" if is_late else ""
            await message.bot.send_message(
                group_id,
                "✅ Topshiriq yakunlandi!\n"
                f"👤 {message.from_user.full_name}\n"
                f"📊 Natija: {score}/{total} ({pct}%)" + late_txt,
            )

        # ✅ (Bu yerga keyin sertifikat yuborish funksiyangizni qo‘shasiz)

        QUIZ.pop(message.from_user.id, None)

        await message.answer(
            f"✅ Tugadi! Natija: {score}/{total} ({pct}%)",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(f"🎯 Siz {xp} XP oldingiz!")
        return

    # =========================
    # ASK QUESTION
    # =========================
    en, correct_uz, opts = qs[i]

    # ko'p tarjima bo'lsa ham, tekshiruv set orqali
    st["correct_set"] = normalize_correct_for_check(correct_uz)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in opts],
        resize_keyboard=True,
    )

    await message.answer(f"❓ {i+1}) {en} — tarjimasi qaysi?", reply_markup=kb)


@router.message(F.text)
async def answer_router(message: Message):
    # commandlar (/, etc) javob sifatida ketib qolmasin
    if (message.text or "").startswith("/"):
        return

    st = QUIZ.get(message.from_user.id)
    if not st:
        return

    ans = (message.text or "").strip()
    correct_set = st.get("correct_set", set())

    ok = ans in correct_set

    # ✅ analytics uchun log
    i = st["i"]
    en, correct_uz, _opts = st["questions"][i]
    st["answers"].append(
        {
            "en": en,
            "correct_uz": correct_uz,
            "chosen": ans,
            "ok": 1 if ok else 0,
        }
    )

    if ok:
        st["score"] += 1
        await message.answer("✅ To‘g‘ri!")
    else:
        await message.answer(f"❌ Noto‘g‘ri. To‘g‘risi: {', '.join(sorted(correct_set))}")

    st["i"] += 1
    await send_question(message)