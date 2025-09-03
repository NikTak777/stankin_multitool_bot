# handlers/help

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from utils.logger import write_user_log
from utils.user_utils import get_user_name

from keyboards.back_to_menu import get_back_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


# Обработчик команды /help
@router.message(Command("help"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_help(message: types.Message):
    full_name = await get_user_name(message)
    help_message = await get_help_text(full_name)

    await message.answer(
        text=help_message,
        reply_markup=get_back_inline_keyboard(),
        parse_mode="Markdown"
    )

    write_user_log(
        f"Пользователь {message.from_user.full_name} ({message.from_user.id}) запросил информацию о боте"
    )


# Обработчик инлайн-кнопки
@router.callback_query(F.data == "help")
@sync_username
async def callback_help(callback: CallbackQuery):
    full_name = await get_user_name(callback.from_user)
    help_message = await get_help_text(full_name)

    await callback.message.edit_text(
        text=help_message,
        reply_markup=get_back_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

    write_user_log(
        f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) запросил информацию о боте"
    )


async def get_help_text(full_name: str) -> str:
    return (
        f"Привет, {full_name}!\n\n"
        "Я — бот Stankin-MultiTool! 🤖\n"
        "Моя задача — помогать студентам Станкина: поздравлять их с днём рождения 🎉 и отправлять актуальное расписание занятий 📅.\n\n"
        "Более подробную информацию о том, что я умею и как устроен, вы можете найти в [GitHub-репозитории](https://github.com/NikTak777/stankin_multitool_bot/)"
    )