from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.edit_profile import get_edit_profile_inline_keyboard
from utils.logger import write_user_log

menu_router = Router()


@menu_router.message(F.data == "edit_profile_menu")
async def profile_menu_callback(clb: CallbackQuery):
    user = clb.from_user
    user_id, full_name, user_name = user.id, user.full_name, user.username

    await clb.message.edit_text(
        text="Выберите, что хотите изменить в профиле:",
        reply_markup=get_edit_profile_inline_keyboard(user_id)
    )

    write_user_log(f"Пользователь {full_name} ({user_id}) @{user_name} перешёл в меню редактирования профиля")
