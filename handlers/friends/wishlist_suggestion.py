# handlers/friends/wishlist_suggestion.py
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError

from utils.logger import write_user_log
from utils.database import get_user_info, update_user_wishlist
from utils.database_utils.friends import (
    add_wishlist_suggestion,
    get_wishlist_suggestion,
    update_wishlist_suggestion_status,
    delete_wishlist_suggestion,
    check_existing_friend
)

from keyboards.friends_menu_keyboards import get_wishlist_suggestion_keyboard
from keyboards.cancel_keyboard import get_cancel_inline_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard

from states.friends_states import WishlistSuggestionState

from bot import bot

from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


@router.callback_query(F.data.startswith("suggest_wishlist:"))
@ensure_user_in_db
@sync_username
async def start_wishlist_suggestion(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс предложения вишлиста другу."""
    user_id = callback.from_user.id
    friend_id = int(callback.data.split(":")[1])
    
    # Проверяем, что пользователь действительно друг
    if not check_existing_friend(user_id, friend_id):
        await callback.answer("Этот пользователь не в вашем списке друзей.", show_alert=True)
        return
    
    friend_info = get_user_info(friend_id)
    if not friend_info:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    
    friend_name = friend_info.get("user_name", "пользователю")
    
    # Сохраняем friend_id в состоянии
    await state.update_data(friend_id=friend_id)
    await state.set_state(WishlistSuggestionState.awaiting_wishlist)
    
    msg_to_user = f"Напишите вишлист, который хотите предложить пользователю {friend_name}:"
    
    await callback.message.edit_text(
        msg_to_user,
        reply_markup=get_cancel_inline_keyboard("friends_edit_menu")
    )
    await callback.answer()
    
    write_user_log(f"Пользователь {callback.from_user.full_name} ({user_id}) начал предлагать вишлист пользователю {friend_name} ({friend_id})")


@router.message(StateFilter(WishlistSuggestionState.awaiting_wishlist))
@sync_username
async def process_wishlist_suggestion(message: Message, state: FSMContext):
    """Обрабатывает введенный вишлист и отправляет предложение другу."""
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    data = await state.get_data()
    friend_id = data.get("friend_id")
    
    if not friend_id:
        await message.answer("Ошибка: не найден получатель. Попробуйте начать заново.",
                           reply_markup=get_back_inline_keyboard("friends_edit_menu"))
        await state.clear()
        return
    
    # Проверяем, что пользователь все еще друг
    if not check_existing_friend(user_id, friend_id):
        await message.answer("Этот пользователь больше не в вашем списке друзей.",
                           reply_markup=get_back_inline_keyboard("friends_edit_menu"))
        await state.clear()
        return
    
    wishlist_text = message.text.strip()
    
    # Валидация длины вишлиста
    if len(wishlist_text) < 2 or len(wishlist_text) > 500:
        await message.answer("Вишлист должен быть от 2 до 500 символов. Попробуйте еще раз.",
                           reply_markup=get_cancel_inline_keyboard("friends_edit_menu"))
        return
    
    friend_info = get_user_info(friend_id)
    if not friend_info:
        await message.answer("Пользователь не найден.",
                           reply_markup=get_back_inline_keyboard("friends_edit_menu"))
        await state.clear()
        return
    
    friend_name = friend_info.get("user_name", "пользователю")
    sender_name = get_user_info(user_id).get("user_name", full_name)
    
    # Добавляем предложение в БД
    suggestion_id = add_wishlist_suggestion(user_id, friend_id, wishlist_text)
    
    try:
        # Отправляем сообщение получателю
        receiver_message = (
            f"🎁 Вам предложили новый вишлист!\n\n"
            f"От: {sender_name}\n"
            f"Вишлист: {wishlist_text}"
        )
        
        await bot.send_message(
            chat_id=friend_id,
            text=receiver_message,
            reply_markup=get_wishlist_suggestion_keyboard(suggestion_id)
        )
        
        # Отправляем подтверждение отправителю
        await message.answer(
            f"✅ Предложенный вишлист отправлен пользователю {friend_name}.",
            reply_markup=get_back_inline_keyboard("friends_edit_menu")
        )
        
        write_user_log(
            f"Пользователь {full_name} ({user_id}) успешно отправил предложение вишлиста "
            f"пользователю {friend_name} ({friend_id})"
        )
        
    except TelegramForbiddenError:
        delete_wishlist_suggestion(suggestion_id)
        await message.answer(
            f"⚠️ Не удалось отправить предложение вишлиста пользователю {friend_name}.\n"
            f"Пользователь, возможно, заблокировал бота.",
            reply_markup=get_back_inline_keyboard("friends_edit_menu")
        )
        write_user_log(
            f"Не удалось отправить предложение вишлиста от {user_id} к {friend_id}: пользователь заблокировал бота"
        )
    except Exception as e:
        delete_wishlist_suggestion(suggestion_id)
        await message.answer(
            f"⚠️ Не удалось отправить предложение вишлиста пользователю {friend_name}.\n"
            f"Попробуйте в другой раз.",
            reply_markup=get_back_inline_keyboard("friends_edit_menu")
        )
        write_user_log(f"Ошибка при отправке предложения вишлиста: {e}")
    
    await state.clear()


@router.callback_query(F.data.startswith("accept_wishlist_suggestion:"))
@sync_username
async def handle_wishlist_suggestion_accept(callback: CallbackQuery):
    """Обрабатывает принятие предложения вишлиста."""
    user_id = callback.from_user.id
    suggestion_id = int(callback.data.split(":")[1])
    
    suggestion = get_wishlist_suggestion(suggestion_id)
    if not suggestion:
        await callback.answer("Предложение не найдено.", show_alert=True)
        return
    
    # Проверяем, что получатель правильный
    if suggestion["receiver_id"] != user_id:
        await callback.answer("Это предложение не для вас.", show_alert=True)
        return
    
    # Проверяем, что предложение еще не обработано
    if suggestion["status"] != "pending":
        await callback.answer("Это предложение уже было обработано.", show_alert=True)
        return
    
    sender_id = suggestion["sender_id"]
    wishlist_text = suggestion["wishlist_text"]
    
    # Обновляем статус предложения
    update_wishlist_suggestion_status(suggestion_id, "accepted")
    
    # Обновляем вишлист пользователя
    update_user_wishlist(user_id, wishlist_text)
    
    sender_info = get_user_info(sender_id)
    sender_name = sender_info.get("user_name", "пользователь") if sender_info else "пользователь"
    receiver_name = get_user_info(user_id).get("user_name", callback.from_user.full_name)
    
    # Уведомляем получателя
    await callback.message.edit_text(
        f"✅ Вы приняли предложенный вишлист от {sender_name}.\n\n"
        f"Ваш новый вишлист: {wishlist_text}",
        reply_markup=get_back_inline_keyboard("start")
    )
    await callback.answer()
    
    # Уведомляем отправителя
    try:
        await bot.send_message(
            chat_id=sender_id,
            text=f"✅ Пользователь {receiver_name} принял ваше предложение вишлиста!",
            reply_markup=get_back_inline_keyboard("friends_edit_menu")
        )
    except Exception as e:
        write_user_log(f"Не удалось отправить уведомление отправителю {sender_id}: {e}")
    
    write_user_log(
        f"Пользователь {receiver_name} ({user_id}) принял предложение вишлиста от "
        f"{sender_name} ({sender_id})"
    )


@router.callback_query(F.data.startswith("decline_wishlist_suggestion:"))
@sync_username
async def handle_wishlist_suggestion_decline(callback: CallbackQuery):
    """Обрабатывает отклонение предложения вишлиста."""
    user_id = callback.from_user.id
    suggestion_id = int(callback.data.split(":")[1])
    
    suggestion = get_wishlist_suggestion(suggestion_id)
    if not suggestion:
        await callback.answer("Предложение не найдено.", show_alert=True)
        return
    
    # Проверяем, что получатель правильный
    if suggestion["receiver_id"] != user_id:
        await callback.answer("Это предложение не для вас.", show_alert=True)
        return
    
    # Проверяем, что предложение еще не обработано
    if suggestion["status"] != "pending":
        await callback.answer("Это предложение уже было обработано.", show_alert=True)
        return
    
    sender_id = suggestion["sender_id"]
    
    # Обновляем статус предложения
    update_wishlist_suggestion_status(suggestion_id, "declined")
    
    sender_info = get_user_info(sender_id)
    sender_name = sender_info.get("user_name", "пользователь") if sender_info else "пользователь"
    receiver_name = get_user_info(user_id).get("user_name", callback.from_user.full_name)
    
    # Уведомляем получателя
    await callback.message.edit_text(
        f"❌ Вы отклонили предложенный вишлист от {sender_name}.",
        reply_markup=get_back_inline_keyboard("start")
    )
    await callback.answer()
    
    # Уведомляем отправителя
    try:
        await bot.send_message(
            chat_id=sender_id,
            text=f"❌ Пользователь {receiver_name} отклонил ваше предложение вишлиста.",
            reply_markup=get_back_inline_keyboard("friends_edit_menu")
        )
    except Exception as e:
        write_user_log(f"Не удалось отправить уведомление отправителю {sender_id}: {e}")
    
    write_user_log(
        f"Пользователь {receiver_name} ({user_id}) отклонил предложение вишлиста от "
        f"{sender_name} ({sender_id})"
    )

