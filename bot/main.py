
###  Botni ran qilish uchun    ========== python -m bot.main ===========

import asyncio
from aiogram import Bot, Dispatcher

from bot.storage.db import init_db
from bot.handlers.teacher import router as teacher_router
from bot.handlers.student import router as student_router
from bot.services.announcer import announcer_loop

# ✅ weekly job importlari
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.services.classroom import (
    list_classes, weekly_top3, week_start_date, mark_weekly_run_if_new
)


def _get_token() -> str:
    # sizda token olish funksiyangiz shu ko‘rinishda bo‘lsa qoldiring
    # (.env orqali oladigan bo'lsa ham shu yerda bo'ladi)
    import os
    from dotenv import load_dotenv
    load_dotenv()
    t = os.getenv("BOT_TOKEN")
    if not t:
        raise RuntimeError("BOT_TOKEN topilmadi. .env ni tekshiring.")
    return t


async def weekly_job(bot: Bot):
    tz = ZoneInfo("Asia/Samarkand")

    while True:
        now = datetime.now(tz)
        print("weekly_job tick:", now)
        # Yakshanba = 6 (Mon=0 ... Sun=6)
        if now.weekday() == 6 and now.hour == 21 and now.minute in (0, 1):
            week_start = week_start_date(now)
            week_end = now.strftime("%Y-%m-%d")

            classes = list_classes()
            for class_id, class_name, group_id in classes:
                # anti-duplicate (har hafta 1 marta)
                if not mark_weekly_run_if_new(class_id, week_start):
                    continue

                top = weekly_top3(class_id, days=7)
                if not top:
                    await bot.send_message(group_id, "🏁 Haftalik yakun: bu hafta ball yig‘ilmagan.")
                    continue

                # Group post
                lines = ["🏆 HAFTALIK TOP-3", f"📅 {week_start} — {week_end}", ""]
                medals = ["🥇", "🥈", "🥉"]
                for i, (_, name, xp) in enumerate(top):
                    lines.append(f"{medals[i]} {name} — {int(xp)} XP")
                await bot.send_message(group_id, "\n".join(lines))


            # shu minutda qayta post bo‘lmasin
            await asyncio.sleep(120)
        else:
            await asyncio.sleep(30)
        

async def main():
    init_db()

    bot = Bot(_get_token())
    dp = Dispatcher()

    dp.include_router(teacher_router)
    dp.include_router(student_router)
    asyncio.create_task(announcer_loop(bot, interval_sec=10))
    # ✅ MANASHU JOY: pollingdan oldin weekly jobni ishga tushiramiz
    asyncio.create_task(weekly_job(bot))

    await dp.start_polling(bot)
    asyncio.create_task(announcer_loop(bot, interval_sec=10))

if __name__ == "__main__":
    asyncio.run(main())