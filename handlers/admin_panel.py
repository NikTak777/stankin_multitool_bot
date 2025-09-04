from aiogram import types, Router, F, Bot
from aiogram.filters import Command

from utils.database import get_real_user_name
from utils.database_utils.database_statistic import get_users_count, count_active_users, count_new_users, get_last_active_users

from keyboards.back_to_menu import get_back_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from decorators.admin_only import admin_only

router = Router()


@router.message(Command("admin_panel"))
@admin_only
@private_only
@ensure_user_in_db
@sync_username
async def cmd_admin_panel(message: types.Message):
    await send_admin_panel(
        bot=message.bot,
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        full_name=message.from_user.full_name,
        message=message,  # передаём message
        callback=None  # не из callback
    )


@router.callback_query(F.data == "admin_panel")
@sync_username
async def handle_admin_panel_callback(callback: types.CallbackQuery):
    await send_admin_panel(
        bot=callback.bot,
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        full_name=callback.from_user.full_name,
        message=callback.message,  # передаём callback.message
        callback=callback  # сигнал, что вызвано из callback
    )
    await callback.answer()


async def send_admin_panel(
        bot: Bot,
        user_id: int,
        chat_id: int,
        full_name: str,
        message: types.Message,
        callback: types.CallbackQuery | None
):
    full_name = get_real_user_name(user_id)
    last_users = get_last_active_users(5)
    names = [u["user_name"] for u in last_users]  # список имён
    text = (
        f"Привет, {full_name}!\n"
        "Это панель управления ботом.\n\n"
        f"👥 Количество пользователей: {get_users_count()}\n"
        f"👥 Количество новых пользователей за неделю: {count_new_users(7)}\n"
        f"👥 Количество уникальных пользователей за неделю: {count_new_users(7)}\n"
        f"👥 Последние активные пользователи:\n- " + "\n- ".join(names)
    )

    if callback:
        await message.edit_text(text=text, reply_markup=get_back_inline_keyboard())
    else:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=get_back_inline_keyboard())