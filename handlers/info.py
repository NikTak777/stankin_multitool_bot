# handlers/info.py
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from utils.logger import write_user_log
from utils.database import get_user_info, check_user_exists
from utils.date_utils import format_date
from keyboards.back_to_menu import get_back_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()

# Обработчик для команды /info
@router.message(Command("info"))
@private_only
@ensure_user_in_db
@sync_username
async def info_command(message: types.Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личной переписке с ботом.")
        return
    await process_user_info(message.from_user, message, is_callback=False)


# Обработчик для инлайн-кнопки (callback_data="info")
@router.callback_query(lambda c: c.data == "info")
async def info_callback(callback: CallbackQuery):
    await callback.answer()
    await process_user_info(callback.from_user, callback.message, is_callback=True)


async def process_user_info(user, message_obj, is_callback=False):

    user_id = user.id
    write_user_log(f"Пользователь {user.full_name} ({user_id}) запросил информацию об аккаунте")
    user_info = get_user_info(user_id)

    if not user_info:
        user_day = user_month = user_year = None
    else:
        user_day = user_info.get("user_day")
        user_month = user_info.get("user_month")
        user_year = user_info.get("user_year")

    if not (user_day and user_month and user_year):
        text = ("Информация не может быть выведена, так как вы не указали дату рождения.\n"
                "Пожалуйста, используйте команду /birthdate для создания аккаунта.")
        if is_callback:
            await message_obj.edit_text(text, reply_markup=get_back_inline_keyboard())
        else:
            await message_obj.answer(text, reply_markup=get_back_inline_keyboard())
        return
    user_nickname = user_info.get("cust_user_name") or "Отсутствует"
    user_wishlist = user_info.get("user_wishlist") or "Отсутствует"
    user_group = user_info.get("user_group") or "Отсутствует"
    user_subgroup = user_info.get("user_subgroup") or "Отсутствует"
    user_subgroup = {"A": "А", "B": "Б"}.get(user_subgroup, user_subgroup) # Преобразуем подгруппу
    formatted_date = format_date(user_day, user_month, user_year) # Форматирование даты

    message_to_user = (
        f"📌 Информация о вашем аккаунте:\n\n"
        f"👤 Имя пользователя: {user.full_name}\n"
        f"🏷 Никнейм: {user_nickname}\n"
        f"🎂 Дата рождения: {formatted_date}\n"
        f"🎁 Вишлист: {user_wishlist}\n"
        f"🏫 Группа: {user_group}\n"
        f"📚 Подгруппа: {user_subgroup}"
    )
    if is_callback:
        await message_obj.edit_text(message_to_user, reply_markup=get_back_inline_keyboard())
    else:
        await message_obj.answer(message_to_user, reply_markup=get_back_inline_keyboard())
    write_user_log(f"Пользователь {user.full_name} ({user_id}) получил информацию об аккаунте")