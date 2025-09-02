from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.logger import write_user_log
from utils.user_utils import get_user_name, is_user_group_admin, is_user_bot_admin
from keyboards.start import get_start_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


@router.message(Command("start"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_start(message: types.Message):
    write_user_log(f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /start")
    await send_start_menu(message)


@router.callback_query(F.data == "start")
@sync_username
async def go_to_start_menu(callback: types.CallbackQuery, state: FSMContext):

    await state.clear()  # Сброс состояния

    await send_start_menu(callback)
    await callback.answer()


async def send_start_menu(message_or_callback, new_message: bool = False):
    """
    Отправляет главное меню пользователю.
    Если new_message=True — всегда отправляет новое сообщение.
    Если False — для callback редактирует сообщение, для message отвечает новым.
    """

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
    is_admin = await is_user_group_admin(user.id)
    inline_keyboard = get_start_inline_keyboard(
        is_group_admin=is_admin,
        is_bot_admin=is_user_bot_admin(user)
    )

    text = f"Привет, {user_name}!\n\nНажми на кнопку, чтобы выбрать действие:"

    if is_callback and not new_message:
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

    write_user_log(f"Пользователь {user.full_name} ({user.id}) открыл стартовое меню")