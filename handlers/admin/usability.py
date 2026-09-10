from aiogram import Router, F
from aiogram.types import CallbackQuery

from services.admin import get_usability_panel
from keyboards.admin_panel import get_admin_panel_keyboard, get_admin_tasks_keyboard
from utils.logger import write_user_log

usability_router = Router()


@usability_router.callback_query(F.data == "usability_panel")
async def usability_panel_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=get_usability_panel(),
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()
    write_user_log(f"Админ {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} открыл панель использования пользователями")