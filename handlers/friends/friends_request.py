# handlers/friends_request.py
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError

from utils.logger import write_user_log
from utils.database import (get_user_info, get_id_from_username, check_user_by_username)

from utils.database_utils.friends import (add_friend_to_user, add_friend_request,
                                          check_existing_request, update_friend_request_status,
                                          get_friend_id_from_request_id, check_existing_friend,
                                          delete_friend_request)

from keyboards.friends_menu_keyboards import get_error_request_keyboard, get_request_keyboard, get_accept_request_keyboard
from keyboards.cancel_keyboard import get_cancel_inline_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard

from bot import bot

# Декораторы
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


@router.callback_query(F.data == "friends_request")
@ensure_user_in_db
@sync_username
async def callback_friends_request(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await process_friends_request(callback.from_user, callback.message, state, is_callback=True)


async def process_friends_request(user, message_obj, state: FSMContext, is_callback=False):
    user_id = user.id
    full_name = user.full_name
    user_name = user.username or "StankinMultiToolBot"

    msg_to_user = f"Пожалуйста, введите тег пользователя, кому вы хотите отправить приглашение в друзья.\nНапример, @{user_name}"

    if is_callback:
        await message_obj.edit_text(msg_to_user, reply_markup=get_cancel_inline_keyboard("friends_menu"))
    else:
        await message_obj.answer(msg_to_user, reply_markup=get_cancel_inline_keyboard("friends_menu"))

    write_user_log(f"Пользователь {full_name} ({user_id}) начал добавлять пользователя в друзья")

    await state.set_state("awaiting_friends")


# Хэндлер, когда пользователь ввёл тег друга
@router.message(StateFilter("awaiting_friends"))
@sync_username
async def send_friend_request(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.username
    full_name = message.from_user.full_name

    friend_tag = message.text.strip().lstrip("@")
    if not (2 <= len(friend_tag) <= 50):
        await message.answer("Тег должен содержать от 2 до 50 символов. Попробуйте еще раз.",
                             reply_markup=get_cancel_inline_keyboard("friends_menu"))
        write_user_log(f"Пользователь {full_name} ({user_id}) ввёл некорректный username")
        return

    if friend_tag == user_name:
        await message.answer(
            text="Себя нельзя добавить в друзья.",
            reply_markup=get_error_request_keyboard()
        )
        write_user_log(f"Пользователь {full_name} ({user_id}) ввёл свой username")
    elif not check_user_by_username(friend_tag):
        await message.answer(
            text="Пользователь не найден.",
            reply_markup=get_error_request_keyboard()
        )
        write_user_log(f"Пользователь {full_name} ({user_id}) ввёл несуществующий username")
    else:
        friend_id = get_id_from_username(friend_tag)[0]

        sender_name = get_user_info(user_id).get("user_name")
        receive_name = get_user_info(friend_id).get("user_name")

        if check_existing_friend(user_id, friend_id):
            write_user_log(f"Пользователь {full_name} ({user_id}) уже является другом пользователя {receive_name} ({friend_id})")
            await message.answer(
                text=f"Вы уже являетесь друзьями с {receive_name}.",
                reply_markup=get_error_request_keyboard()
            )
            return

        # Проверяем, не отправлял ли уже запрос
        existing_request = check_existing_request(user_id, friend_id)
        if existing_request:
            write_user_log(f"Пользователь {full_name} ({user_id}) отправил повторный запрос пользователю {receive_name} ({friend_id})")
            await message.answer(
                text=f"Вы уже отправили запрос пользователю {receive_name}.",
                reply_markup=get_error_request_keyboard()
            )
            return

        # Добавляем новый запрос
        request_id = add_friend_request(user_id, friend_id)

        try:
            msg = f"Пользователь {sender_name} отправил Вам запрос в друзья!"
            await bot.send_message(
                chat_id=friend_id,
                text=msg,
                reply_markup=get_request_keyboard(request_id)
            )

            await message.answer(f"Ваш запрос пользователю {receive_name} был успешно отправлен!\n"
                                 f"Вам придёт уведомление, когда будет ответ.",
                                 reply_markup=get_back_inline_keyboard("friends_menu"))

            write_user_log(f"Пользователь {full_name} ({user_id}) успешно отправил запрос пользователю {receive_name} {(friend_id)}")

        except TelegramForbiddenError:
            delete_friend_request(request_id)
            await message.answer(
                f"⚠️ Не удалось отправить запрос пользователю {receive_name}.\n"
                f"Пользователь, возможно, заблокировал меня(",
                reply_markup=get_error_request_keyboard()
            )
        except Exception as e:
            delete_friend_request(request_id)
            await message.answer(
                f"⚠️ Не удалось отправить запрос пользователю {receive_name}.\n"
                f"Попробуйте в другой раз.",
                reply_markup=get_error_request_keyboard()
            )

    await state.clear()


@router.callback_query(F.data.startswith("accept_friend_request:"))
@sync_username
async def handle_friend_request_accept(callback: CallbackQuery):
    user_id = callback.from_user.id
    request_id = get_request_id_from_callback(callback)  # Получаем ID запроса

    # Обновляем статус запроса на "accepted"
    update_friend_request_status(request_id, "accepted")

    # Получаем ID друга из запроса
    friend_id = get_friend_id_from_request_id(request_id)

    # Добавляем обоих пользователей в друзья
    add_friend_to_user(user_id, friend_id)
    add_friend_to_user(friend_id, user_id)

    receive_name = get_user_info(user_id).get("user_name")
    sender_name = get_user_info(friend_id).get("user_name")

    await callback.message.edit_text(f"Вы стали друзьями c пользователем {sender_name}!",
                                     reply_markup=get_accept_request_keyboard())
    await callback.answer()

    text = f"Пользователь {receive_name} принял Ваш запрос в друзья!"
    await bot.send_message(chat_id=friend_id, text=text, reply_markup=get_accept_request_keyboard())

    write_user_log(
        f"Пользователь {receive_name} ({user_id}) принял запрос пользователя {sender_name} ({friend_id})")


@router.callback_query(F.data.startswith("decline_friend_request:"))
@sync_username
async def handle_friend_request_decline(callback: CallbackQuery):
    user_id = callback.from_user.id
    request_id = get_request_id_from_callback(callback)

    update_friend_request_status(request_id, "declined")

    friend_id = get_friend_id_from_request_id(request_id)

    receive_name = get_user_info(user_id).get("user_name")
    sender_name = get_user_info(friend_id).get("user_name")

    await callback.message.edit_text(f"Вы отклонили запрос пользователя {sender_name}!",
                                     reply_markup=get_accept_request_keyboard())
    await callback.answer()

    text = f"Пользователь {receive_name} отклонил Ваш запрос в друзья!"
    await bot.send_message(chat_id=friend_id, text=text)

    write_user_log(
        f"Пользователь {receive_name} ({user_id}) отклонил запрос пользователя {sender_name} ({friend_id})")


def get_request_id_from_callback(callback: CallbackQuery) -> int:
    return int(callback.data.split(":")[1])  # "accept_friend_request:123" -> 123
