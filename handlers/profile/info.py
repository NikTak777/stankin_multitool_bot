from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.profile_menu_keyboard import get_profile_menu_inline_keyboard
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from services.profile.info import get_profile_info_text
from utils.logger import write_user_log


info_router = Router()


@info_router.message(Command("info"))
@private_only
@ensure_user_in_db
@sync_username
async def profile_info_command(msg: Message):
    user = msg.from_user
    user_id, full_name, user_name = user.id, user.full_name, user.username

    await msg.answer(
        text=get_profile_info_text(user_id),
        reply_markup=get_profile_menu_inline_keyboard()
    )

    write_user_log(
        f"Пользователь {full_name} ({user_id}) @{user_name} "
        f"ввёл команду /info"
    )


@info_router.callback_query(F.data == "profile-info")
@private_only
@ensure_user_in_db
@sync_username
async def profile_info_callback(clb: CallbackQuery):
    user = clb.from_user
    user_id, full_name, user_name = user.id, user.full_name, user.username

    await clb.message.edit_text(
        text=get_profile_info_text(user_id),
        reply_markup=get_profile_menu_inline_keyboard()
    )

    write_user_log(
        f"Пользователь {full_name} ({user_id}) @{user_name} "
        f"открыл информацию о своём профиле"
    )
