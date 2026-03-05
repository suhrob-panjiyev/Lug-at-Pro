import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from bot.storage.db import init_db
from bot.handlers.teacher import router as teacher_router
from bot.handlers.student import router as student_router
from bot.services.announcer import announcer_loop

from datetime import datetime
from zoneinfo import ZoneInfo
from bot.services.classroom import (
    list_classes, weekly_top3, week_start_date, mark_weekly_run_if_new
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is required")

# ✅ Secret path: URL topib yubormaslik uchun
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change_me")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
dp.include_router(teacher_router)
dp.include_router(student_router)

app = FastAPI()


async def weekly_job(bot: Bot):
    tz = ZoneInfo("Asia/Samarkand")
    while True:
        now = datetime.now(tz)
        if now.weekday() == 6 and now.hour == 21 and now.minute in (0, 1):
            week_start = week_start_date(now)
            week_end = now.strftime("%Y-%m-%d")

            classes = list_classes()
            for class_id, class_name, group_id in classes:
                if not mark_weekly_run_if_new(class_id, week_start):
                    continue

                top = weekly_top3(class_id, days=7)
                if not top:
                    await bot.send_message(group_id, "🏁 Haftalik yakun: bu hafta ball yig‘ilmagan.")
                    continue

                lines = ["🏆 HAFTALIK TOP-3", f"📅 {week_start} — {week_end}", ""]
                medals = ["🥇", "🥈", "🥉"]
                for i, (_, name, xp) in enumerate(top):
                    lines.append(f"{medals[i]} {name} — {int(xp)} XP")
                await bot.send_message(group_id, "\n".join(lines))

            await asyncio.sleep(120)
        else:
            await asyncio.sleep(30)


@app.on_event("startup")
async def on_startup():
    init_db()

    # ✅ background tasklar (polling o‘rniga)
    asyncio.create_task(announcer_loop(bot, interval_sec=10))
    asyncio.create_task(weekly_job(bot))

    # ✅ Deploydan keyin Render sizga public URL beradi
    base_url = os.getenv("BASE_URL")
    if base_url:
        # Telegram webhookni avtomatik qo'yamiz
        await bot.set_webhook(url=base_url.rstrip("/") + WEBHOOK_PATH)


@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    try:
        data = await req.json()
        update = Update.model_validate(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid update")

    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}