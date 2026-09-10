from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from services.admin import get_summary_panel
from keyboards.admin_panel import get_admin_panel_keyboard, get_admin_tasks_keyboard
from utils.logger import write_user_log

summary_router = Router()


@summary_router.message(Command("admin_panel"))
async def admin_panel_command(message: Message):
    await message.answer(
        text=get_summary_panel(user_id=message.from_user.id),
        reply_markup=get_admin_panel_keyboard()
    )
    write_user_log(f"Админ {message.from_user.full_name} ({message.from_user.id}) @{message.from_user.username} ввёл команду /admin_panel")


@summary_router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=get_summary_panel(user_id=callback.from_user.id),
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()
    write_user_log(f"Админ {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} открыл панель админа")