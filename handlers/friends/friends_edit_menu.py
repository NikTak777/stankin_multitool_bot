from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.user_utils import get_user_name
from utils.database_utils.friends import get_friends_info

from keyboards.friends_menu_keyboards import get_edit_menu_keyboard

from states.friends_states import EditMenuState

from decorators.sync_username import sync_username

from utils.logger import write_user_log

router = Router()


@router.callback_query(F.data == "friends_edit_menu")
@sync_username
async def callback_friends_edit_menu(callback: CallbackQuery, state: FSMContext):
    """
    Вход в меню редактирования друзей. Инициализируем индекс только если его нет.
    """
    # Очищаем состояние перед входом в меню (на случай, если были другие состояния)
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    await state.clear()

    await state.set_state(EditMenuState.editing)
    # Восстанавливаем индекс, если он был
    await state.update_data(current_index=current_index)

    await update_friends_view(callback, state)
    await callback.answer()

    write_user_log(
        f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} перешёл во вкладку редактирования друзей"
    )


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

    selected_fid, selected_name = pairs[idx]

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

    await callback.message.edit_text(text, reply_markup=get_edit_menu_keyboard(total, selected_fid))
