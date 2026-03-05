from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/chatid")
async def chatid(message: Message):
    await message.answer(
        f"Chat ID: {message.chat.id}\nUser ID: {message.from_user.id}"
    )