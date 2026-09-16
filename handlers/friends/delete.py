from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.logger import write_user_log

from handlers.friends.friends_edit_menu import update_friends_view

from decorators.sync_username import sync_username

from services.friends.delete import delete_friend_service

delete_router = Router()


@delete_router.callback_query(F.data == "delete_friend")
@sync_username
async def callback_delete_friends(callback: CallbackQuery, state: FSMContext):
    """
    Удаляет текущего друга.
    """
    user = callback.from_user
    user_id = user.id
    full_name = user.full_name
    user_name = user.username
    data = await state.get_data()
    idx = int(data.get("current_index", 0))

    result = delete_friend_service(user_id, idx)

    await update_friends_view(
        callback=callback,
        state=state,
        prefix=result.prefix_msg
    )
    await state.update_data(current_index=result.index)
    await callback.answer(text=result.alert)

    if result.status == "not_found":
        write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                       f"не смог удалить друга, список друзей пуст")
    elif result.status == "delete_last":
        write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                       f"удалил из друзей пользователя {result.friend_name} ({result.friend_id}), список друзей пуст")
    else:
        write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                       f"удалил из друзей пользователя {result.friend_name} ({result.friend_id})")
