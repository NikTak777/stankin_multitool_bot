from aiogram import types, Router
from aiogram.filters import Command
from utils.logger import write_user_log
from utils.user_utils import get_user_name
from keyboards.start import get_start_inline_keyboard
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()

@router.message(Command("start"))
@private_only
@ensure_user_in_db
@sync_username
async def start_msg(message: types.Message):
    await send_start_menu(message)


@router.callback_query(lambda c: c.data == "start")
async def go_to_start_menu(callback: types.CallbackQuery):
    await send_start_menu(callback)
    await callback.answer()


async def send_start_menu(message_or_callback):
    if isinstance(message_or_callback, types.Message):
        user = message_or_callback.from_user
        message_obj = message_or_callback
        is_callback = False

    elif isinstance(message_or_callback, types.CallbackQuery):
        user = message_or_callback.from_user
        message_obj = message_or_callback.message
        is_callback = True
    else:
        return

    user_name = await get_user_name(user)
    inline_keyboard = get_start_inline_keyboard()

    text = f"Привет, {user_name}! Нажми на кнопку, чтобы выбрать действие:"

    if is_callback:
        # Для callback - редактируем существующее сообщение бота
        await message_obj.edit_text(
            text,
            reply_markup=inline_keyboard
        )
    else:
        # Для команды /start - отправляем новое сообщение
        await message_obj.answer(
            text,
            reply_markup=inline_keyboard
        )