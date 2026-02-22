import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.storage.db import get_conn


def _build_start_button(bot_username: str, assignment_id: int) -> InlineKeyboardMarkup:
    # Sizning student.py da payload: /start hw_<id> ishlaydi ✅
    url = f"https://t.me/{bot_username}?start=hw_{assignment_id}"
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Testni boshlash", url=url)
    return kb.as_markup()


async def announcer_loop(bot: Bot, interval_sec: int = 10):
    me = await bot.get_me()
    bot_username = me.username  # masalan: LugatProBot
    print("🔁 announcer tick")
    print("📌 announcer db =", __import__("bot.storage.db").storage.db.DB_PATH)
    while True:
        try:
            conn = get_conn()
            cur = conn.cursor()

            # pending announcementlarni olamiz
            cur.execute("""
                SELECT a.id, a.class_id, a.assignment_id, c.group_id, c.name
                FROM announcements a
                JOIN classes c ON c.id = a.class_id
                WHERE a.status='pending'
                ORDER BY a.id ASC
                LIMIT 5
            """)
            rows = cur.fetchall()

            for r in rows:
                ann_id = r["id"] if isinstance(r, dict) or hasattr(r, "keys") else r[0]
                class_id = r["class_id"] if isinstance(r, dict) or hasattr(r, "keys") else r[1]
                assignment_id = r["assignment_id"] if isinstance(r, dict) or hasattr(r, "keys") else r[2]
                group_id = r["group_id"] if isinstance(r, dict) or hasattr(r, "keys") else r[3]
                class_name = r["name"] if isinstance(r, dict) or hasattr(r, "keys") else r[4]

                try:
                    kb = _build_start_button(bot_username, int(assignment_id))
                    text = (
                        f"📢 Yangi topshiriq!\n"
                        f"🏫 Sinf: {class_name}\n"
                        f"🆔 Assignment: {assignment_id}\n\n"
                        f"👇 Testni boshlash uchun tugmani bosing:"
                    )
                    await bot.send_message(chat_id=int(group_id), text=text, reply_markup=kb)

                    cur.execute(
                        "UPDATE announcements SET status='sent', sent_at=CURRENT_TIMESTAMP, error=NULL WHERE id=?",
                        (ann_id,),
                    )
                    conn.commit()
                except Exception as e:
                    cur.execute(
                        "UPDATE announcements SET status='error', error=? WHERE id=?",
                        (str(e)[:500], ann_id),
                    )
                    conn.commit()

            conn.close()

        except Exception:
            # katta yiqilish bo‘lsa ham loop to‘xtamasin
            pass

        await asyncio.sleep(interval_sec)