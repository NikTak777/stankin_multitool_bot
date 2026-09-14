from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramForbiddenError

from services.admin import get_usability_panel
from keyboards.admin_panel import get_admin_panel_keyboard
from utils.logger import write_user_log

usability_router = Router()


@usability_router.callback_query(F.data == "usability_panel")
async def usability_panel_callback(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            text=get_usability_panel(),
            reply_markup=get_admin_panel_keyboard()
        )
        await callback.answer()
        write_user_log(
            f"Админ {callback.from_user.full_name} ({callback.from_user.id}) "
            f"@{callback.from_user.username} открыл панель использования пользователями"
        )
    except TelegramForbiddenError:
        write_user_log(
            f"Ошибка вывода панели использования пользователями у админа {callback.from_user.full_name} "
            f"({callback.from_user.id}) @{callback.from_user.username}. Сообщение не обновлено."
        )