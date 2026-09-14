from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramForbiddenError

from services.admin import get_activity_panel
from keyboards.admin_panel import get_admin_panel_keyboard
from utils.logger import write_user_log

activity_router = Router()


@activity_router.callback_query(F.data == "activity_panel")
async def activity_panel_callback(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            text=get_activity_panel(),
            reply_markup=get_admin_panel_keyboard()
        )
        await callback.answer()
        write_user_log(f"Админ {callback.from_user.full_name} ({callback.from_user.id}) "
                       f"@{callback.from_user.username} открыл панель активности пользователей"
        )
    except TelegramForbiddenError:
        write_user_log(
            f"Ошибка вывода панели активности пользователей у админа {callback.from_user.full_name} "
            f"({callback.from_user.id}) @{callback.from_user.username}. Сообщение не обновлено."
        )
