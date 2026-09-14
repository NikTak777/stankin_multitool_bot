# handlers/friends_request.py
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError

from utils.logger import write_user_log
from utils.database import (get_user_info)

from utils.database_utils.friends import (add_friend_to_user, update_friend_request_status,
                                          get_friend_id_from_request_id, delete_friend_request)

from keyboards.friends_menu_keyboards import get_error_request_keyboard, get_request_keyboard, get_accept_request_keyboard
from keyboards.cancel_keyboard import get_cancel_inline_keyboard

from services.friends.request import (
    get_friend_request_text,
    get_friend_request_accept_text,
    FriendRequestStatus
)

from bot import bot

from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

request_router = Router()


@request_router.callback_query(F.data == "friends_request")
@ensure_user_in_db
@sync_username
async def callback_friends_request(clb: CallbackQuery, state: FSMContext):
    user_id = clb.from_user.id
    full_name = clb.from_user.full_name
    user_name = clb.from_user.username or "StankinMultiToolBot"

    await clb.message.edit_text(
        text=f"Введите тег пользователя, кому вы хотите отправить приглашение в друзья.\nНапример, @{user_name}",
        reply_markup=get_cancel_inline_keyboard("friends_menu")
    )
    write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} начал ввод юзернейма пользователя для добавления в друзья")

    await clb.answer()
    await state.set_state("awaiting_friends")


@request_router.message(StateFilter("awaiting_friends"))
@sync_username
async def send_friend_request(message: Message, state: FSMContext):
    search_username = message.text
    user_id = message.from_user.id
    user_name = message.from_user.username
    full_name = message.from_user.full_name

    status, msg_to_user, request_id, friend_id = get_friend_request_text(
        search_username=search_username,
        own_username=message.from_user.username,
        own_user_id=user_id
    )

    if status == FriendRequestStatus.SUCCESS:
        try:
            await bot.send_message(
                chat_id=friend_id,
                text=f"Пользователь {full_name} @{user_name} отправил Вам запрос в друзья!",
                reply_markup=get_request_keyboard(request_id)
            )
            await message.answer(
                text=msg_to_user,
                reply_markup=get_cancel_inline_keyboard("friends_menu")
            )
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                           f"успешно отправил запрос пользователю {search_username} ({friend_id})")
        except TelegramForbiddenError as e:
            delete_friend_request(request_id)
            await message.answer(
                f"⚠️ Не удалось отправить запрос пользователю {search_username}.\n"
                f"Пользователь, возможно, заблокировал меня 😔",
                reply_markup=get_error_request_keyboard()
            )
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                           f"не смог отправить запрос пользователю {search_username} ({friend_id}). "
                           f"Причина: Бот заблокирован ({e})")
        except Exception as e:
            delete_friend_request(request_id)
            await message.answer(
                f"⚠️ Не удалось отправить запрос пользователю {search_username}.\n"
                f"Попробуйте в другой раз.",
                reply_markup=get_error_request_keyboard()
            )
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                           f"не смог отправить запрос пользователю {search_username} ({friend_id}). "
                           f"Неизвестная ошибка: {e}")
        await state.clear()

    elif status == FriendRequestStatus.INVALID:
        await message.answer(
            text=msg_to_user,
            reply_markup=get_cancel_inline_keyboard("friends_menu")
        )
        write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} ввёл некорректный username {search_username}")

    elif status in (FriendRequestStatus.SELF_ADD, FriendRequestStatus.NOT_FOUND,
                  FriendRequestStatus.ALREADY_FRIENDS, FriendRequestStatus.REQUEST_EXISTS):
        await message.answer(
            text=msg_to_user,
            reply_markup=get_error_request_keyboard()
        )
        if status == FriendRequestStatus.SELF_ADD:
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} ввёл свой username")
        elif status == FriendRequestStatus.NOT_FOUND:
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                           f"ввёл несуществующий username {search_username}")
        elif status == FriendRequestStatus.ALREADY_FRIENDS:
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                           f"уже является другом пользователя {search_username} ({friend_id})")
        else:
            write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                           f"отправил повторный запрос пользователю {search_username} ({friend_id})")
        await state.clear()


@request_router.callback_query(F.data.startswith("accept_friend_request:"))
@sync_username
async def handle_friend_request_accept(callback: CallbackQuery):
    receiver_id = callback.from_user.id
    request_id = int(callback.data.split(":")[1])

    (
        receiver_req_text,
        sender_req_text,
        log_text,
        sender_id

    ) = get_friend_request_accept_text(
        receiver_id=receiver_id,
        request_id=request_id
    )

    await callback.message.edit_text(
        text=receiver_req_text,
        reply_markup=get_accept_request_keyboard()
    )
    await callback.answer()
    write_user_log(log_text)

    try:
        await bot.send_message(
            chat_id=sender_id,
            text=sender_req_text,
            reply_markup=get_accept_request_keyboard())

    except TelegramForbiddenError:
        write_user_log(f"Не удалось доставить уведомление пользователю "
                       f"{sender_id}: бот заблокирован")
    except Exception as e:
        write_user_log(f"Не удалось доставить уведомление пользователю "
                       f"{sender_id}: {e}")


@request_router.callback_query(F.data.startswith("decline_friend_request:"))
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
