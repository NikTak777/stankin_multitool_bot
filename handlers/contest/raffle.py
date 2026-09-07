from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from decorators.admin_only import admin_only
from decorators.sync_username import sync_username

from services.contest import start_raffle

raffle_router = Router()


@raffle_router.message(Command("contest"))
@sync_username
@admin_only
async def start_raffle(message: Message):
    win_user_id = start_raffle()
    await message.answer(
        text=f"Выиграл пользователь {win_user_id}"
    )
