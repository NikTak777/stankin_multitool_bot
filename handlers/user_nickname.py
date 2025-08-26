from aiogram import types, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from utils.logger import write_user_log
from utils.database import update_cust_user_name

from keyboards.cancel_keyboard import get_cancel_inline_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


# Обработчик команды /nickname
@router.message(Command("nickname"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_user_nickname(message: types.Message, state: FSMContext):

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /nickname"
    write_user_log(msg)

    await process_user_nickname(message.from_user, message, state, is_callback=False)


# Обработчик callback-кнопки
@router.callback_query(F.data == "nickname")
async def callback_user_nickname(callback: CallbackQuery, state: FSMContext):

    msg = f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку для ввода никнейма"
    write_user_log(msg)

    await callback.answer()
    await process_user_nickname(callback.from_user, callback.message, state, is_callback=True)


# Универсальная функция для ввода нового никнейма
async def process_user_nickname(user, message_obj, state: FSMContext, is_callback=False):

    msg_to_user = f"Пожалуйста, введите ваш новый никнейм:"

    if is_callback:
        await message_obj.edit_text(msg_to_user, reply_markup=get_cancel_inline_keyboard("edit_profile_menu"))
    else:
        await message_obj.answer(msg_to_user, reply_markup=get_cancel_inline_keyboard("edit_profile_menu"))

    await state.set_state("awaiting_user_nickname")


@router.message(StateFilter("awaiting_user_nickname"))
async def show_user_nickname(message: types.Message, state: FSMContext):

    new_wishlist = message.text.strip()

    if len(new_wishlist) < 2 or len(new_wishlist) > 20:  # Пример проверки длины вишлиста
        await message.answer("Никнейм должен быть от 2 до 20 символов. Попробуйте еще раз.")
        return

    UserID = message.from_user.id

    update_cust_user_name(UserID, new_wishlist)

    await message.answer(f"Ваш новый никнейм успешно сохранен: {new_wishlist}", reply_markup=get_back_inline_keyboard("info"))
    msg = f"Пользователь {message.from_user.full_name} ({UserID}) установил новый никнейм: {new_wishlist}"
    write_user_log(msg)
    await state.clear()