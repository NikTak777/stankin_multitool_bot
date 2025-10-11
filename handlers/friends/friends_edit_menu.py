from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.user_utils import get_user_name
from utils.database_utils.friends import get_friends_info

from keyboards.friends_menu_keyboards import get_edit_menu_keyboard

from states.friends_states import EditMenuState

from decorators.sync_username import sync_username

router = Router()


@router.callback_query(F.data == "friends_edit_menu")
@sync_username
async def callback_friends_edit_menu(callback: CallbackQuery, state: FSMContext):
    """
    Вход в меню редактирования друзей. Инициализируем индекс и показываем список.
    """
    await state.set_state(EditMenuState.editing)
    await state.update_data(current_index=0)
    await update_friends_view(callback, state)
    await callback.answer()


@router.callback_query(EditMenuState.editing, F.data.in_(["friends_prev", "friends_next"]))
@sync_username
async def friends_nav(callback: CallbackQuery, state: FSMContext):
    """
    Листаем список друзей (вперёд/назад).
    """
    user_id = callback.from_user.id
    friends = get_friends_info(user_id)
    total = len(friends)

    if total <= 1:
        await callback.answer()  # Нечего листать
        return

    # текущее состояние
    data = await state.get_data()
    idx = int(data.get("current_index", 0))

    # определяем направление
    idx = (idx - 1) % total if callback.data == "friends_prev" else (idx + 1) % total

    # сохраняем новый индекс и обновляем экран
    await state.update_data(current_index=idx)
    await update_friends_view(callback, state)
    await callback.answer()


async def update_friends_view(callback: CallbackQuery, state: FSMContext, prefix: str = ""):
    """
    Рендерит список друзей, подсвечивая текущего индикатором
    и показывает базовый заголовок.
    """
    data = await state.get_data()
    idx = int(data.get("current_index", 0))

    user = callback.from_user
    user_name = await get_user_name(user)
    pairs = get_friends_info(user.id)
    total = len(pairs)

    if total == 0:
        message_text = f"Привет, {user_name}!\n\nУ тебя пока нет друзей."
        await callback.message.edit_text(message_text, reply_markup=get_edit_menu_keyboard(total))
        return

    # нормализуем индекс
    if idx >= total:
        idx = 0
        await state.update_data(current_index=idx)

    # подсветка текущего
    lines = []
    for i, (fid, name) in enumerate(pairs):
        prefix_icon = "👉" if i == idx else "👤"
        lines.append(f"{prefix_icon} {name}")

    text = (
        f"{prefix}"
        f"Привет, {user_name}!\n\n"
        f"Твои друзья ({idx+1}/{total}):\n" +
        "\n".join(lines)
    )

    await callback.message.edit_text(text, reply_markup=get_edit_menu_keyboard(total))
