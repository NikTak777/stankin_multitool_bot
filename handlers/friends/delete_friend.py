from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.database_utils.friends import get_friends_info, delete_friend

from handlers.friends.friends_edit_menu import update_friends_view

from keyboards.back_to_menu import get_back_inline_keyboard

from decorators.sync_username import sync_username

from utils.logger import write_user_log

router = Router()


@router.callback_query(F.data == "delete_friend")
@sync_username
async def callback_delete_friends(callback: CallbackQuery, state: FSMContext):
    """
    Удаляет текущего друга.
    """
    user_id = callback.from_user.id
    pairs = get_friends_info(user_id)
    total = len(pairs)

    if total == 0:
        await callback.answer("Список пуст.")
        return

    data = await state.get_data()
    idx = int(data.get("current_index", 0))
    # нормализуем индекс
    if idx >= total:
        idx = 0

    friend_id, friend_name = pairs[idx]
    delete_friend(user_id, friend_id)

    # после удаления перечитываем список и чиним индекс
    pairs2 = get_friends_info(user_id)
    total2 = len(pairs2)
    if total2 == 0:
        await state.update_data(current_index=0)
        await callback.message.edit_text(
            f"Друг «{friend_name}» удалён.\n\nСписок пуст.",
            reply_markup=get_back_inline_keyboard("friends_menu"))
        await callback.answer("Удалено")
        return

    # если индекс указывает за конец — сдвинем на предыдущий элемент
    if idx >= total2 and total2 > 0:
        idx = total2 - 1

    await state.update_data(current_index=idx)
    await update_friends_view(callback, state, prefix=f"🗑 Удалил: {friend_name}\n\n")
    await callback.answer("Удалено")

    write_user_log(
        f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} "
        f"удалил друга {friend_name}"
    )
