# handlers/friends/friend_profile.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.friends_states import EditMenuState
from utils.database_utils.friends import get_friends_info
from utils.database import get_user_info
from utils.date_utils import format_date
from utils.database_utils.database_statistic import get_user_rank_by_activity, get_user_rank_by_days
from keyboards.back_to_menu import get_back_inline_keyboard
from decorators.sync_username import sync_username

router = Router()


@router.callback_query(EditMenuState.editing, F.data == "friend_profile")
@sync_username
async def callback_friend_profile(callback: CallbackQuery, state: FSMContext):
    """
    Показывает профиль текущего (подсвеченного) друга.
    Берём current_index из FSM, получаем friend_id и рендерим карточку.
    """
    user_id = callback.from_user.id

    pairs = get_friends_info(user_id)
    total = len(pairs)
    if total == 0:
        await callback.message.edit_text("У тебя пока нет друзей.", reply_markup=get_back_inline_keyboard("friends_edit_menu"))
        await callback.answer()
        return

    data = await state.get_data()
    idx = int(data.get("current_index", 0))
    if idx >= total:
        idx = 0
        await state.update_data(current_index=idx)

    friend_id, friend_name = pairs[idx]

    info = get_user_info(friend_id) or {}
    user_name = info.get("user_tag")
    user_name = f"@{user_name}" if user_name else ""
    day = info.get("user_day")
    month = info.get("user_month")
    year = info.get("user_year")

    wishlist = info.get("user_wishlist") or "Отсутствует"
    group = info.get("user_group") or "Отсутствует"
    subgroup = info.get("user_subgroup") or "Отсутствует"
    subgroup = {"A": "А", "B": "Б"}.get(subgroup, subgroup)

    if not day or not month or not year:
        bday_str = "Отсутствует"
    else:
        bday_str = format_date(day, month, year)

    # Получаем метрики друга
    rank_activity = get_user_rank_by_activity(friend_id)
    rank_days = get_user_rank_by_days(friend_id)
    
    rank_activity_text = f"#{rank_activity}" if rank_activity > 0 else "Нет данных"
    rank_days_text = f"#{rank_days}" if rank_days > 0 else "Нет данных"

    text = (
        f"👤 Профиль {friend_name} {user_name}\n\n"
        f"🎂 Дата рождения: {bday_str}\n"
        f"🎁 Вишлист: {wishlist}\n"
        f"🏫 Группа: {group}\n"
        f"📚 Подгруппа: {subgroup}\n\n"
        f"📊 Статистика:\n"
        f"🎯 Место в топе по действиям: {rank_activity_text}\n"
        f"📅 Место в топе по дням: {rank_days_text}"
    )

    # Создаем клавиатуру с кнопкой "Предложить вишлист"
    from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎁 Предложить вишлист",
        callback_data=f"suggest_wishlist:{friend_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="friends_edit_menu"
    ))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()