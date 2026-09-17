from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from services.profile.statistics import get_user_statistics_text
from keyboards.back_to_menu import get_back_inline_keyboard
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from utils.logger import write_user_log

stats_router = Router()


@stats_router.message(Command("stats", "statistics"))
@private_only
@ensure_user_in_db
@sync_username
async def show_statistics_command(msg: Message):
    user = msg.from_user
    user_id, full_name, user_name = user.id, user.full_name, user.username

    await msg.answer(
        text=get_user_statistics_text(user_id),
        reply_markup=get_back_inline_keyboard("profile-info")
    )

    write_user_log(
        f"Пользователь {full_name} ({user_id}) @{user_name} "
        f"ввёл команду /statistics"
    )


@stats_router.callback_query(F.data == "statistics")
@private_only
@ensure_user_in_db
@sync_username
async def show_statistics_callback(clb: CallbackQuery):
    user = clb.from_user
    user_id, full_name, user_name = user.id, user.full_name, user.username

    await clb.message.edit_text(
        text=get_user_statistics_text(user_id),
        reply_markup=get_back_inline_keyboard("profile-info")
    )

    write_user_log(
        f"Пользователь {full_name} ({user_id}) @{user_name} "
        f"открыл статистику профиля"
    )
