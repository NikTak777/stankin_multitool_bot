from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from utils.logger import write_user_log
from utils.user_utils import get_user_name
from keyboards.edit_profile import get_edit_profile_inline_keyboard

from decorators.sync_username import sync_username

router = Router()


@router.callback_query(lambda c: c.data == "edit_profile_menu")
@sync_username
async def edit_profile_menu(callback: types.CallbackQuery, state: FSMContext):

    await state.clear()  # Сброс состояния

    user_id = callback.from_user.id
    user_name = await get_user_name(callback)

    write_user_log(f"Пользователь {callback.from_user.full_name} ({user_id}) перешёл в меню редактирования профиля")

    inline_keyboard = get_edit_profile_inline_keyboard()

    await callback.message.edit_text(
        f"Привет, {user_name}!\n\nВыбери, что хочешь изменить в профиле:",
        reply_markup=inline_keyboard
    )

    await callback.answer() # Убрать эффект загрузки
