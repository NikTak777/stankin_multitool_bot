from aiogram import types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from utils.logger import write_user_log
from utils.database import get_user_info, get_user_wishlist

from keyboards.friend_wishlist_keyboard import get_error_wishlist_keyboard
from keyboards.cancel_keyboard import get_cancel_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from decorators.require_birthdate import require_birthdate

from services.friend_wishlist_service import (
    birthday_missing_text,
    friend_wishlist_prompt,
    own_wishlist_message,
    friend_wishlist_not_found,
    friend_wishlist_empty,
    friend_wishlist_info
)

router = Router()

# Обработчик команды /friend_wishlist
@router.message(Command("friend_wishlist"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_friend_wishlist(message: types.Message, state: FSMContext):

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /friend_wishlist"
    write_user_log(msg)

    await process_friend_wishlist(message.from_user, message, state, is_callback=False)


# Обработчик callback-кнопки
@router.callback_query(lambda c: c.data == "friend_wishlist")
@sync_username
async def callback_friend_wishlist(callback: CallbackQuery, state: FSMContext):

    msg = f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку для просмотра вишлиста друга"
    write_user_log(msg)

    await callback.answer()
    await process_friend_wishlist(callback.from_user, callback.message, state, is_callback=True)


# Универсальная функция для запроса тега друга
@require_birthdate("friend_wishlist")
async def process_friend_wishlist(user, message_obj, state: FSMContext, is_callback=False):
    user_id = user.id
    user_info = get_user_info(user_id)

    user_tag = user_info.get("user_tag")
    msg_to_user = f"Пожалуйста, введите тег пользователя, чей вишлист вы хотите посмотреть.\nНапример, @{user_tag}" if user_tag else "Пожалуйста, введите тег пользователя, чей вишлист вы хотите посмотреть.\nНапример, @StankinMultiToolBot"

    if is_callback:
        await message_obj.edit_text(msg_to_user, reply_markup=get_cancel_inline_keyboard("start"))
    else:
        await message_obj.answer(msg_to_user, reply_markup=get_cancel_inline_keyboard("start"))

    await state.set_state("awaiting_friend_wishlist")


# Хэндлер, когда пользователь ввёл тег друга
@router.message(StateFilter("awaiting_friend_wishlist"))
async def show_friend_wishlist(message: types.Message, state: FSMContext):

    friend_tag = message.text.strip().lstrip("@")
    if not (2 <= len(friend_tag) <= 50):
        await message.answer("Тег должен содержать от 2 до 50 символов. Попробуйте еще раз.")
        return

    user_id = message.from_user.id
    user_info = get_user_info(user_id)
    user_tag = user_info.get("user_tag")
    result = get_user_wishlist(friend_tag)

    if friend_tag == user_tag:
        msg_to_user = own_wishlist_message(user_info.get("user_wishlist"))
        await message.answer(
            text=f"Хм, вы ввели свой собственный тег. Пытаетесь проверить сами себя? 😉\n\n{msg_to_user}",
            reply_markup=get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) запросил свой же вишлист")
    elif result == "not_found":
        await message.answer(
            text=friend_wishlist_not_found(friend_tag),
            reply_markup=get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) не смог узнать вишлист, @{friend_tag} не найден")
    elif isinstance(result, tuple) and result[1] == "no_wishlist":
        friend_name = result[0] or ""
        await message.answer(
            text=friend_wishlist_empty(friend_name, friend_tag),
            reply_markup=get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) запросил вишлист @{friend_tag}, но его нет")
    else:
        friend_name, friend_wishlist = result
        friend_name = friend_name or ""
        await message.answer(
            text=friend_wishlist_info(friend_name, friend_tag, friend_wishlist),
            reply_markup = get_error_wishlist_keyboard()
        )
        write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) получил вишлист @{friend_tag}")

    await state.clear()
