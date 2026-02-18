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

FRIENDS_PER_PAGE = 10


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
    Листаем выбранного друга в списке (вперёд/назад в пределах страницы или глобально).
    """
    user_id = callback.from_user.id
    friends = get_friends_info(user_id)
    total = len(friends)

    if total <= 1:
        await callback.answer()
        return

    data = await state.get_data()
    idx = int(data.get("current_index", 0))
    idx = (idx - 1) % total if callback.data == "friends_prev" else (idx + 1) % total
    await state.update_data(current_index=idx)
    await update_friends_view(callback, state)
    await callback.answer()


@router.callback_query(EditMenuState.editing, F.data.in_(["friends_page_prev", "friends_page_next"]))
@sync_username
async def friends_page_nav(callback: CallbackQuery, state: FSMContext):
    """
    Переключение страниц списка друзей (по 10 на страницу).
    """
    user_id = callback.from_user.id
    friends = get_friends_info(user_id)
    total = len(friends)
    total_pages = (total + FRIENDS_PER_PAGE - 1) // FRIENDS_PER_PAGE if total else 0

    if total_pages <= 1:
        await callback.answer()
        return

    data = await state.get_data()
    idx = int(data.get("current_index", 0))
    current_page = idx // FRIENDS_PER_PAGE

    if callback.data == "friends_page_prev":
        new_page = (current_page - 1) if current_page > 0 else (total_pages - 1)  # с первой влево → последняя
    else:
        new_page = (current_page + 1) if current_page < total_pages - 1 else 0  # с последней вправо → первая

    new_idx = new_page * FRIENDS_PER_PAGE
    await state.update_data(current_index=new_idx)
    await update_friends_view(callback, state)
    await callback.answer()


async def update_friends_view(callback: CallbackQuery, state: FSMContext, prefix: str = ""):
    """
    Рендерит список друзей по страницам (до FRIENDS_PER_PAGE на страницу),
    подсвечивает текущего выбранного друга.
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

    if idx >= total:
        idx = 0
        await state.update_data(current_index=idx)

    total_pages = (total + FRIENDS_PER_PAGE - 1) // FRIENDS_PER_PAGE
    current_page = idx // FRIENDS_PER_PAGE
    start = current_page * FRIENDS_PER_PAGE
    end = min(start + FRIENDS_PER_PAGE, total)
    pairs_page = pairs[start:end]

    lines = []
    for i, (fid, name) in enumerate(pairs_page):
        global_i = start + i
        prefix_icon = "👉" if global_i == idx else "👤"
        lines.append(f"{prefix_icon} {name}")

    page_info = f"Страница {current_page + 1} из {total_pages}" if total_pages > 1 else ""
    range_info = f"Друзья {start + 1}-{end} из {total}"
    header = f"Твои друзья ({range_info})"
    if page_info:
        header += f"\n{page_info}"

    text = f"{prefix}Привет, {user_name}!\n\n{header}:\n" + "\n".join(lines)

    selected_fid = pairs[idx][0]
    await callback.message.edit_text(
        text,
        reply_markup=get_edit_menu_keyboard(
            total, selected_fid,
            total_pages=total_pages,
            current_page=current_page
        )
    )
