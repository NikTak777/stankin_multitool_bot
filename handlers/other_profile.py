from aiogram import types, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from utils.logger import write_user_log
from utils.database import get_user_info, get_id_from_username

from keyboards.friend_wishlist_keyboard import get_error_wishlist_keyboard
from keyboards.cancel_keyboard import get_cancel_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from decorators.require_birthdate import require_birthdate

from services.other_profile_service import (
    get_own_profile_info,
    other_user_not_found,
    other_profile_info
)

router = Router()

# Обработчик команды /friend_profile
@router.message(Command("friend_profile"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_other_profile(message: types.Message, state: FSMContext):

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /friend_profile"
    write_user_log(msg)

    await process_other_profile(message.from_user, message, state, is_callback=False)


# Обработчик callback-кнопки
@router.callback_query(F.data == "other_profile")
@sync_username
async def callback_friend_profile(callback: CallbackQuery, state: FSMContext):

    msg = f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку для просмотра чужого профиля"
    write_user_log(msg)

    await callback.answer()
    await process_other_profile(callback.from_user, callback.message, state, is_callback=True)


# Универсальная функция для запроса тега
@require_birthdate("friend_wishlist")
async def process_other_profile(user, message_obj, state: FSMContext, is_callback=False):
    user_name = user.username or "StankinMultiToolBot"
    msg_to_user = f"Пожалуйста, введите тег пользователя, чей профиль вы хотите посмотреть.\nНапример, @{user_name}"

    if is_callback:
        await message_obj.edit_text(msg_to_user, reply_markup=get_cancel_inline_keyboard("start"))
    else:
        await message_obj.answer(msg_to_user, reply_markup=get_cancel_inline_keyboard("start"))

    await state.set_state("awaiting_other_profile")


# Хэндлер, когда пользователь ввёл тег
@router.message(StateFilter("awaiting_other_profile"))
async def show_other_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.username

    other_user_name = message.text.strip().lstrip("@")
    if not (2 <= len(other_user_name) <= 50):
        await message.answer("Тег должен содержать от 2 до 50 символов. Попробуйте еще раз.")
        return

    other_id = get_id_from_username(other_user_name)[0]

    info = get_user_info(other_id)

    if other_user_name == user_name:
        msg_to_user = get_own_profile_info(info)
        await message.answer(
            text=msg_to_user,
            reply_markup=get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) запросил свой же профиль")
    elif info is None:
        await message.answer(
            text=other_user_not_found(other_user_name),
            reply_markup=get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) не смог получить профиль, @{other_user_name} не найден")
    else:
        await message.answer(
            text=other_profile_info(info),
            reply_markup = get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) получил профиль @{other_user_name}")

    await state.clear()
