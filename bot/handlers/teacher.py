from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from bot.services.certificate import get_certificate_safe_path
from aiogram.types import FSInputFile

from aiogram.types import FSInputFile
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ChatMemberUpdated,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.storage.db import get_conn
from bot.services.classroom import (
    create_assignment,
    get_class_by_group,
    set_assignment_questions,
    weekly_top3,
)
from bot.services.quiz import build_fixed_quiz

# Sertifikat (sizning xizmat formatiga mos)

router = Router()
TZ = ZoneInfo("Asia/Samarkand")


# =========================
# Teacher Panel Buttons
# =========================
BTN_CREATE = "🏫 Sinfni yaratish"
BTN_GIVEHW = "🧪 Topshiriq berish"
BTN_STATUS = "📊 Status"
BTN_WEEKLY = "🏆 Weekly top"
BTN_DAILY = "🏅 Daily top"
BTN_CERT_TEST = "🧾 Sertifikat test"
BTN_GET_CERT = "🏅 Sertifikatni olish"
BTN_HIDE = "🙈 Panelni yashirish"
BTN_CANCEL = "⬅️ Bekor qilish"


def teacher_panel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CREATE), KeyboardButton(text=BTN_GIVEHW)],
            [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_WEEKLY)],
            [KeyboardButton(text=BTN_DAILY), KeyboardButton(text=BTN_CERT_TEST)],
            [KeyboardButton(text=BTN_GET_CERT)],
            [KeyboardButton(text=BTN_HIDE)],
        ],
        resize_keyboard=True,
        selective=False,
        is_persistent=True,
        input_field_placeholder="Teacher paneldan tanlang 👇",
    )


# =========================
# GiveHW FSM (Wizard)
# =========================
class GiveHW(StatesGroup):
    n_questions = State()
    deadline = State()


def normalize_deadline(inp: str) -> str | None:
    """
    Qabul qiladi:
      - "14:00" (HH:MM)
      - "30m", "1h", "2h"
      - "yo‘q", "yoq", "none" -> None
    Qaytaradi: "HH:MM" yoki None
    """
    s = (inp or "").strip().lower()

    if s in {"yo‘q", "yoq", "none", "-", "no"}:
        return None

    # HH:MM
    if re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", s):
        return s

    now = datetime.now(TZ)
    if s == "30m":
        t = now + timedelta(minutes=30)
        return f"{t.hour:02d}:{t.minute:02d}"
    if s == "1h":
        t = now + timedelta(hours=1)
        return f"{t.hour:02d}:{t.minute:02d}"
    if s == "2h":
        t = now + timedelta(hours=2)
        return f"{t.hour:02d}:{t.minute:02d}"

    return None


# =========================
# Panel auto ko‘rsatish (bot guruhga qo‘shilganda)
# =========================
@router.my_chat_member()
async def on_my_chat_member(update: ChatMemberUpdated):
    """
    Bot guruhga qo‘shilganda (yoki status o'zgarganda) panel chiqarib beradi.
    """
    try:
        chat = update.chat
        new_status = update.new_chat_member.status
        old_status = update.old_chat_member.status
    except Exception:
        return

    if chat.type not in ("group", "supergroup"):
        return

    # "member" yoki "administrator" bo'lib qolsa => bot endi guruhda
    if old_status in ("left", "kicked") and new_status in ("member", "administrator"):
        try:
            await update.bot.send_message(
                chat.id,
                "👨‍🏫 Teacher panel yoqildi.",
                reply_markup=teacher_panel_kb(),
            )
        except Exception:
            pass


# =========================
# Core логикалар (komanda/tugma ikkalasi ishlatsin)
# =========================
async def do_create_class(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Sinf yaratish faqat guruhda mumkin.")
        return

    teacher_id = message.from_user.id
    group_id = message.chat.id
    class_name = message.chat.title or "Class"

    existing = get_class_by_group(group_id)
    if existing:
        await message.answer("Bu guruh uchun sinf allaqachon yaratilgan.", reply_markup=teacher_panel_kb())
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO classes (name, group_id, teacher_id) VALUES (?, ?, ?)",
        (class_name, group_id, teacher_id),
    )
    class_id = cur.lastrowid
    conn.commit()
    conn.close()

    bot_username = (await message.bot.me()).username
    join_link = f"https://t.me/{bot_username}?start=join_{class_id}"

    await message.answer(
        "✅ Sinf yaratildi!\n\n"
        f"O‘quvchilar qo‘shilish linki:\n{join_link}\n\n"
        "👨‍🏫 Teacher panel yoqildi.",
        reply_markup=teacher_panel_kb(),
    )


async def do_give_hw(message: Message, n_questions: int, deadline_hhmm: str | None):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Bu buyruq faqat guruhda ishlaydi.")
        return

    cls = get_class_by_group(message.chat.id)
    if not cls:
        await message.answer("Avval /create_class qiling.", reply_markup=teacher_panel_kb())
        return

    class_id = cls[0]

    # 1) assignment yaratamiz
    assignment_id = create_assignment(class_id, n_questions, deadline_hhmm=deadline_hhmm)

    # 2) fixed quiz (hamma uchun bir xil) yaratib DB ga saqlaymiz
    fixed = build_fixed_quiz(n_questions, seed=assignment_id, k_options=4)
    set_assignment_questions(assignment_id, fixed)

    bot_username = (await message.bot.me()).username
    start_link = f"https://t.me/{bot_username}?start=hw_{assignment_id}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🚀 Testni boshlash", url=start_link)]]
    )

    await message.answer(
        "📌 Yangi topshiriq berildi!\n"
        f"📝 Savollar: {n_questions}\n"
        f"⏰ Deadline: {deadline_hhmm or 'yo‘q'}\n\n"
        "O‘quvchilar boshlashi uchun tugma 👇",
        reply_markup=kb,
    )
    # panelni yana ko'rsatib qo'yamiz (UX)
    await message.answer("✅ Tayyor.", reply_markup=teacher_panel_kb())


async def do_daily_top(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    conn = get_conn()
    cur = conn.cursor()

    today = date.today().isoformat()

    cur.execute(
        """
        SELECT full_name, SUM(xp) as total
        FROM xp_log
        WHERE DATE(created_at)=?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
        """,
        (today,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await message.answer("Bugun hali ball yig‘ilmagan.")
        return

    text = "🏅 BUGUNGI TOP:\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (name, total) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i+1}."
        text += f"{prefix} {name} — {total} XP\n"

    await message.answer(text)


async def do_weekly_top(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    conn = get_conn()
    cur = conn.cursor()

    week_ago = (datetime.now(TZ) - timedelta(days=7)).strftime("%Y-%m-%d")

    cur.execute(
        """
        SELECT full_name, SUM(xp) as total
        FROM xp_log
        WHERE DATE(created_at)>=?
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT 10
        """,
        (week_ago,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await message.answer("Haftalik ball hali yo‘q.")
        return

    text = "🏆 HAFTALIK TOP:\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (name, total) in enumerate(rows):
        prefix = medals[i] if i < 3 else f"{i+1}."
        text += f"{prefix} {name} — {total} XP\n"

    await message.answer(text)


async def do_status(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Bu buyruq faqat guruhda ishlaydi.")
        return

    cls = get_class_by_group(message.chat.id)
    if not cls:
        await message.answer("Avval /create_class qiling.", reply_markup=teacher_panel_kb())
        return

    class_id = cls[0]

    conn = get_conn()
    cur = conn.cursor()

    # active assignment
    cur.execute(
        """
        SELECT id, n_questions, deadline_hhmm, deadline_at
        FROM assignments
        WHERE class_id=? AND is_active=1
        ORDER BY id DESC LIMIT 1
        """,
        (class_id,),
    )
    a = cur.fetchone()

    if not a:
        conn.close()
        await message.answer("Aktiv topshiriq yo‘q.", reply_markup=teacher_panel_kb())
        return

    assignment_id, n_q, deadline_hhmm, deadline_at = a

    # members
    cur.execute(
        "SELECT user_id, full_name FROM members WHERE class_id=? ORDER BY joined_at ASC",
        (class_id,),
    )
    members = cur.fetchall()

    # attempts
    cur.execute(
        """
        SELECT user_id, full_name, score, total, pct, is_late, answers_json
        FROM attempts
        WHERE class_id=? AND assignment_id=?
        """,
        (class_id, assignment_id),
    )
    attempts = cur.fetchall()
    conn.close()

    done_map = {
        uid: (name, score, total, pct, is_late, answers_json)
        for (uid, name, score, total, pct, is_late, answers_json) in attempts
    }

    done, late, pending = [], [], []

    note = ""
    if not members and attempts:
        note = (
            "\nℹ️ Eslatma: members ro'yxati bo'sh. "
            "O'quvchilar join link orqali qo'shilsa pending ham ko'rinadi."
        )
        for uid, name, *_rest in attempts:
            is_late = int(done_map.get(uid, (None, None, None, None, 0, None))[4] or 0)
            (late if is_late else done).append(name)
    else:
        for uid, name in members:
            if uid in done_map:
                is_late = int(done_map[uid][4] or 0)
                (late if is_late else done).append(name)
            else:
                pending.append(name)

    # avg score
    avg = 0.0
    if attempts:
        avg = sum((r[2] or 0) for r in attempts) / len(attempts)

    # analytics: most missed questions (top 5)
    miss_counter = Counter()
    for r in attempts:
        answers_json = r[6]
        if not answers_json:
            continue
        try:
            answers = json.loads(answers_json)
        except Exception:
            continue
        for it in answers:
            if int(it.get("ok", 0)) == 0:
                en = str(it.get("en", "")).strip()
                if en:
                    miss_counter[en] += 1

    top_missed = miss_counter.most_common(5)

    text = (
        f"📌 STATUS — Assignment #{assignment_id}\n"
        f"📝 Savollar: {n_q}\n"
        f"⏰ Deadline: {deadline_hhmm or 'yo‘q'}\n\n"
        f"✅ Topshirganlar: {len(done)} ta\n"
        f"⏰ Kech topshirganlar: {len(late)} ta\n"
        f"⏳ Hali topshirmaganlar: {len(pending)} ta\n"
        f"📊 O‘rtacha ball: {avg:.2f}/{n_q}\n"
    )

    if note:
        text += note

    if done:
        text += "\n\n✅ Topshirganlar:\n" + "\n".join(f"• {n}" for n in done[:30])
        if len(done) > 30:
            text += f"\n… (+{len(done)-30} ta)"
    if late:
        text += "\n\n⏰ Kech topshirganlar:\n" + "\n".join(f"• {n}" for n in late[:30])
        if len(late) > 30:
            text += f"\n… (+{len(late)-30} ta)"
    if pending:
        text += "\n\n⏳ Hali topshirmaganlar:\n" + "\n".join(f"• {n}" for n in pending[:30])
        if len(pending) > 30:
            text += f"\n… (+{len(pending)-30} ta)"

    if top_missed:
        text += "\n\n🔥 Eng ko‘p xato qilingan so‘zlar (Top-5):\n"
        for en, c in top_missed:
            text += f"• {en} — {c} ta xato\n"

    await message.answer(text, reply_markup=teacher_panel_kb())


# =========================
# Sertifikat test (panel tugmasi va /test_cert)
# =========================
from datetime import datetime

from aiogram.types import FSInputFile

from aiogram.types import FSInputFile

async def do_cert_test(message):
    # png = get_certificate_safe_path()
    img_path = get_certificate_safe_path()
    await message.answer_photo(FSInputFile(str(img_path)), caption="✅ Sertifikat (MVP)")

# =========================
# Sertifikatni olish (oxirgi aktiv assignment bo‘yicha)
# =========================
async def do_get_cert(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Bu tugma faqat guruhda ishlaydi.")
        return

    cls = get_class_by_group(message.chat.id)
    if not cls:
        await message.answer("Avval sinf yarating (🏫 Sinfni yaratish).", reply_markup=teacher_panel_kb())
        return

    class_id = cls[0]

    conn = get_conn()
    cur = conn.cursor()

    # oxirgi aktiv assignment
    cur.execute(
        """
        SELECT id, n_questions
        FROM assignments
        WHERE class_id=? AND is_active=1
        ORDER BY id DESC LIMIT 1
        """,
        (class_id,),
    )
    a = cur.fetchone()
    if not a:
        conn.close()
        await message.answer("Aktiv topshiriq yo‘q.", reply_markup=teacher_panel_kb())
        return

    assignment_id, total = a

    # Sertifikat kimga? (hozircha teacher o'zi uchun test variant)
    cur.execute(
        """
        SELECT score, total, pct
        FROM attempts
        WHERE class_id=? AND assignment_id=? AND user_id=?
        ORDER BY id DESC LIMIT 1
        """,
        (class_id, assignment_id, message.from_user.id),
    )
    r = cur.fetchone()
    conn.close()

    if not r:
        await message.answer(
            "Siz bu topshiriqni hali topshirmagansiz.\n"
            "Test uchun o‘zingiz topshirib ko‘ring, keyin sertifikat oling.",
            reply_markup=teacher_panel_kb(),
        )
        return

    score, total2, pct = int(r[0]), int(r[1]), float(r[2])

# =========================
# /panel (ixtiyoriy qoldiramiz)
# =========================
@router.message(Command("panel"))
async def panel_cmd(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Panel faqat guruhda ishlaydi 🙂")
        return
    await message.answer("👨‍🏫 Teacher panel yoqildi.", reply_markup=teacher_panel_kb())


@router.message(F.text == BTN_HIDE)
async def hide_panel(message: Message):
    await message.answer("Panel yashirildi.", reply_markup=ReplyKeyboardRemove())


# =========================
# Command handlers
# =========================
@router.message(Command("create_class"))
async def create_class_cmd(message: Message):
    await do_create_class(message)


@router.message(Command("give_hw"))
async def give_hw_cmd(message: Message):
    # eski format: /give_hw 10 23:00 (deadline ixtiyoriy)
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Bu buyruq faqat guruhda ishlaydi.")
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Format: /give_hw 10 23:00 (deadline ixtiyoriy)")
        return

    try:
        n_questions = int(parts[1])
    except Exception:
        await message.answer("Savollar soni son bo‘lishi kerak. Masalan: /give_hw 10 23:00")
        return

    deadline_inp = parts[2] if len(parts) >= 3 else None
    deadline = normalize_deadline(deadline_inp) if deadline_inp else None

    await do_give_hw(message, n_questions=n_questions, deadline_hhmm=deadline)


@router.message(Command("daily_top"))
async def daily_top_cmd(message: Message):
    await do_daily_top(message)


@router.message(Command("weekly_top"))
async def weekly_top_cmd(message: Message):
    await do_weekly_top(message)


@router.message(Command("test_cert"))
async def test_cert_cmd(message: Message):
    await do_cert_test(message)


@router.message(Command("status"))
async def status_cmd(message: Message):
    await do_status(message)


# =========================
# Panel button handlers
# =========================
@router.message(F.text == BTN_CREATE)
async def create_class_btn(message: Message):
    await do_create_class(message)


@router.message(F.text == BTN_STATUS)
async def status_btn(message: Message):
    await do_status(message)


@router.message(F.text == BTN_WEEKLY)
async def weekly_btn(message: Message):
    await do_weekly_top(message)


@router.message(F.text == BTN_DAILY)
async def daily_btn(message: Message):
    await do_daily_top(message)


@router.message(F.text == BTN_CERT_TEST)
async def cert_test_btn(message: Message):
    await do_cert_test(message)


@router.message(F.text == BTN_GET_CERT)
async def get_cert_btn(message: Message):
    await do_get_cert(message)


# =========================
# GiveHW Wizard (tugma -> FSM)
# =========================
@router.message(F.text == BTN_GIVEHW)
async def give_hw_start(message: Message, state: FSMContext):
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("Topshiriq faqat guruhda beriladi 🙂")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="5"), KeyboardButton(text="10"), KeyboardButton(text="15")],
            [KeyboardButton(text="20"), KeyboardButton(text="30")],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        selective=True,
        is_persistent=True,
    )
    await state.set_state(GiveHW.n_questions)
    await message.answer("🧪 Nechta savol beramiz?", reply_markup=kb)


@router.message(F.text == BTN_CANCEL)
async def give_hw_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=teacher_panel_kb())


@router.message(GiveHW.n_questions, F.text.regexp(r"^\d+$"))
async def give_hw_set_n(message: Message, state: FSMContext):
    n = int(message.text.strip())
    if n < 1 or n > 50:
        await message.answer("1–50 oralig‘ida tanlang.")
        return

    await state.update_data(n_questions=n)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="14:00"), KeyboardButton(text="21:00"), KeyboardButton(text="23:00")],
            [KeyboardButton(text="30m"), KeyboardButton(text="1h"), KeyboardButton(text="2h")],
            [KeyboardButton(text="yo‘q")],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        selective=True,
        is_persistent=True,
    )
    await state.set_state(GiveHW.deadline)
    await message.answer("⏰ Deadline tanlang (yoki 30m/1h/2h, yoki yo‘q):", reply_markup=kb)


@router.message(GiveHW.n_questions)
async def give_hw_bad_n(message: Message):
    await message.answer("Iltimos, savollar sonini raqam bilan tanlang. Masalan: 10")


@router.message(GiveHW.deadline)
async def give_hw_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    n = int(data["n_questions"])

    dl = normalize_deadline(message.text or "")
    if dl is None and (message.text or "").strip().lower() not in {"yo‘q", "yoq", "none", "-", "no"}:
        await message.answer("Deadline noto‘g‘ri. Masalan: 14:00 yoki 30m/1h/2h yoki yo‘q")
        return

    await state.clear()
    await do_give_hw(message, n_questions=n, deadline_hhmm=dl)