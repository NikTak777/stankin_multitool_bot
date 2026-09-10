from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from services.admin import get_task_panel, TASK_NAMES
from keyboards.admin_panel import get_admin_tasks_keyboard
from utils.logger import write_user_log
from utils.database_utils.task_management import toggle_task

task_router = Router()


@task_router.callback_query(F.data == "task_panel")
async def task_panel_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=get_task_panel(),
        reply_markup=get_admin_tasks_keyboard()
    )
    await callback.answer()
    write_user_log(f"Админ {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} открыл панель переключения таск")


@task_router.callback_query(F.data.startswith("toggle_task:"))
async def handle_toggle_task(callback: CallbackQuery):
    task_key = callback.data.split(":")[1]

    task_display_name = TASK_NAMES.get(task_key, task_key)

    new_status = toggle_task(task_key)

    status_text = "включен" if new_status else "выключен"
    await callback.answer(f"Таск '{task_display_name}' {status_text}", show_alert=True)

    write_user_log(
        f"Админ {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} "
        f"{'включил' if new_status else 'выключил'} таск '{task_display_name}'"
    )

    try:
        await callback.message.edit_text(
            text=get_task_panel(),
            reply_markup=get_admin_tasks_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise