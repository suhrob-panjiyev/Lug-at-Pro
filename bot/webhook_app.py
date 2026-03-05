import os
import asyncio
from fastapi import FastAPI, Request, HTTPException, Header
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

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change_me")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"

BASE_URL = os.getenv("BASE_URL")  # https://lugatpro-bot.onrender.com
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")  # web panel himoyasi

def check_admin(x_api_key: str | None):
    if ADMIN_API_KEY and x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
    asyncio.create_task(announcer_loop(bot, interval_sec=10))
    asyncio.create_task(weekly_job(bot))

    if BASE_URL:
        await bot.set_webhook(url=BASE_URL.rstrip("/") + WEBHOOK_PATH)


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


# -------------------------
# ✅ WEB PANEL API
# -------------------------

@app.get("/api/bot/kpis")
def api_kpis(x_api_key: str | None = Header(default=None)):
    check_admin(x_api_key)
    from bot.storage.db_admin import bot_kpis
    return bot_kpis()

from fastapi import Header, HTTPException
import logging

@app.get("/api/classes")
def api_classes(x_api_key: str | None = Header(default=None)):
    check_admin(x_api_key)
    try:
        from bot.storage.db_admin import list_classes_admin
        return list_classes_admin()
    except Exception as e:
        logging.exception("api_classes failed")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

@app.post("/api/assignments/create")
def api_create_assignment(payload: dict, x_api_key: str | None = Header(default=None)):
    check_admin(x_api_key)
    from bot.storage.db_admin import create_assignment_web

    class_id = int(payload["class_id"])
    n_questions = int(payload["n_questions"])
    deadline_hhmm = payload.get("deadline_hhmm")
    deactivate_prev = bool(payload.get("deactivate_prev", True))

    aid = create_assignment_web(class_id, n_questions, deadline_hhmm, deactivate_prev=deactivate_prev)
    return {"ok": True, "assignment_id": aid}

@app.post("/api/classes/create")
def api_create_class(payload: dict, x_api_key: str | None = Header(default=None)):
    check_admin(x_api_key)
    from bot.storage.db_admin import create_class_web

    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    group_id = int(payload["group_id"])
    teacher_id = int(payload["teacher_id"])

    cid = create_class_web(name, group_id, teacher_id)
    return {"ok": True, "class_id": cid}