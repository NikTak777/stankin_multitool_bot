from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.friends.friends_edit_menu import update_friends_view
from states.friends_states import EditMenuState
from utils.logger import write_user_log
from decorators.sync_username import sync_username
from keyboards.friends_menu_keyboards import get_friend_profile_keyboard
from services.friends.profile import friend_profile_service

profile_router = Router()


@profile_router.callback_query(EditMenuState.editing, F.data == "friend_profile")
@sync_username
async def callback_friend_profile(callback: CallbackQuery, state: FSMContext):
    """
    Показывает профиль текущего (подсвеченного) друга.
    Берём current_index из FSM, получаем friend_id и рендерим карточку.
    """
    user = callback.from_user
    user_id = user.id
    full_name = user.full_name
    user_name = user.username
    data = await state.get_data()
    index = int(data.get("current_index", 0))

    result = friend_profile_service(
        user_id=user_id,
        index=index
    )
    await state.update_data(current_index=result.index)

    if result.status == "not_found":
        await callback.answer(text=result.msg_to_user)
        await update_friends_view(
            callback=callback,
            state=state
        )
        write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                       f"не смог посмотреть профиль друга, список друзей пуст")
        return

    await callback.message.edit_text(
        text=result.msg_to_user,
        reply_markup=get_friend_profile_keyboard(result.friend_id)
    )
    await callback.answer()
    write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} "
                   f"посмотрел профиль друга {result.friend_name} ({result.friend_id})")