from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from decorators.admin_only import admin_only
from decorators.sync_username import sync_username

from utils.user_utils import get_user_name
from utils.database import get_user_info

from services.contest import start_raffle, get_all_contest_stats

from keyboards.contest import get_admin_contest_menu_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard

raffle_router = Router()


@raffle_router.message(Command("contest"))
@sync_username
@admin_only
async def admin_contest_menu_command(message: Message):
    user_name = await get_user_name(message.from_user)
    await message.answer(
        text=(
            f"Привет, {user_name}!\n\n"
            f"{get_all_contest_stats()}"
        ),
        reply_markup=get_admin_contest_menu_keyboard()
    )


@raffle_router.callback_query(F.data == "contest-panel")
@sync_username
@admin_only
async def admin_contest_menu_callback_query(callback: CallbackQuery):
    user_name = await get_user_name(callback.from_user)
    await callback.message.edit_text(
        text=(
            f"Привет, {user_name}!\n\n"
            f"{get_all_contest_stats()}"
        ),
        reply_markup=get_admin_contest_menu_keyboard()
    )
    await callback.answer()


@raffle_router.callback_query(F.data == "start-raffle")
@sync_username
@admin_only
async def start_contest_raffle_handler(callback: CallbackQuery):
    winner_id = start_raffle()
    winner_info = get_user_info(winner_id)
    winner_fullname, winner_username = winner_info["user_name"], winner_info["user_tag"]
    await callback.message.edit_text(
        text=(
            f"Победителем стал: {winner_fullname} @{winner_username}\n\n"
            f"{get_all_contest_stats()}"
        ),
        reply_markup=get_back_inline_keyboard()
    )
    await callback.answer()
