# handlers/friends/friend_profile.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.friends_states import EditMenuState
from utils.database_utils.friends import get_friends_info
from utils.database import get_user_info
from utils.date_utils import format_date
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

    text = (
        f"👤 Профиль {friend_name}\n\n"
        f"🎂 Дата рождения: {bday_str}\n"
        f"🎁 Вишлист: {wishlist}\n"
        f"🏫 Группа: {group}\n"
        f"📚 Подгруппа: {subgroup}"
    )

    await callback.message.edit_text(text, reply_markup=get_back_inline_keyboard("friends_edit_menu"))
    await callback.answer()