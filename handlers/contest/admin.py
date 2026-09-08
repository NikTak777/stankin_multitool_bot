from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from decorators.admin_only import admin_only
from decorators.sync_username import sync_username

from utils.user_utils import get_user_name

from services.contest import start_raffle, get_all_contest_stats

from keyboard.contest import get_admin_contest_menu_keyboard

raffle_router = Router()


@raffle_router.message(Command("contest"))
@sync_username
@admin_only
async def admin_contest_menu_command(message: Message):
    user_name = await get_user_name(message.from_user.id)
    await message.answer(
        text=f"Привет, {user_name}!\n\n"
             f"{get_all_contest_stats()}",
        reply_markup=get_admin_contest_menu_keyboard()
    )
