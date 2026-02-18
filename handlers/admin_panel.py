from aiogram import types, Router, F, Bot
from aiogram.filters import Command

from utils.database import get_real_user_name
from utils.database_utils.database_statistic import get_users_count, count_active_users, count_new_users, get_last_active_users, get_top_active_users, get_top_users_by_days
from utils.database_utils.task_management import toggle_task, get_task_status
from utils.logger import write_user_log

from keyboards.back_to_menu import get_back_inline_keyboard
from keyboards.admin_tasks_keyboard import get_admin_tasks_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from decorators.admin_only import admin_only

router = Router()


@router.message(Command("admin_panel"))
@admin_only
@private_only
@ensure_user_in_db
@sync_username
async def cmd_admin_panel(message: types.Message):
    await send_admin_panel(
        bot=message.bot,
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        full_name=message.from_user.full_name,
        message=message,  # передаём message
        callback=None  # не из callback
    )


@router.callback_query(F.data == "admin_panel")
@sync_username
async def handle_admin_panel_callback(callback: types.CallbackQuery):
    await send_admin_panel(
        bot=callback.bot,
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        full_name=callback.from_user.full_name,
        message=callback.message,  # передаём callback.message
        callback=callback  # сигнал, что вызвано из callback
    )
    await callback.answer()


async def send_admin_panel(
        bot: Bot,
        user_id: int,
        chat_id: int,
        full_name: str,
        message: types.Message,
        callback: types.CallbackQuery | None
):
    full_name = get_real_user_name(user_id)

    # Получаем топ-5 последних пользователей
    last_users = get_last_active_users(10)
    last_users_text = "\n".join([
        f"{i+1}. {u['user_name']} @{u['user_tag']}"
        for i, u in enumerate(last_users)
    ])

    # Получаем топ-5 активных пользователей
    top_users = get_top_active_users(5)
    top_users_text = "\n".join([
        f"{i+1}. {u['user_name']} @{u['user_tag']} ({u['activity_count']} событий)"
        for i, u in enumerate(top_users)
    ])
    
    # Получаем топ-5 пользователей по количеству дней использования
    top_days_users = get_top_users_by_days(5)
    top_days_text = "\n".join([
        f"{i+1}. {u['user_name']} @{u['user_tag']} ({u['days_count']} дней)"
        for i, u in enumerate(top_days_users)
    ])
    
    # Создаем клавиатуру с кнопками управления
    from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⚙️ Управление тасками",
        callback_data="admin_tasks"
    ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад в меню",
        callback_data="start"
    ))
    
    text = (
        f"Привет, {full_name}!\n"
        "Это панель управления ботом.\n\n"
        f"👥 Количество пользователей: {get_users_count()}\n"
        f"👥 Количество новых пользователей за неделю: {count_new_users(7)}\n"
        f"👥 Количество уникальных пользователей за неделю: {count_active_users(7)}\n"
        f"👥 Последние активные пользователи:\n{last_users_text}\n\n"
        f"🏆 Топ-5 самых активных пользователей за всё время:\n{top_users_text}\n\n"
        f"📅 Топ-5 пользователей по количеству дней использования:\n{top_days_text}"
    )

    if callback:
        await message.edit_text(text=text, reply_markup=builder.as_markup())
    else:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=builder.as_markup())


async def _update_admin_tasks_menu(message: types.Message):
    """Обновляет меню управления тасками (вспомогательная функция)."""
    task_names = {
        "daily_schedule": "📅 Ежедневная рассылка расписания",
        "birthday_notifications": "🎂 Уведомления о днях рождения",
        "new_year_greetings": "🎄 Новогодние поздравления",
        "schedule_notifications": "⏰ Уведомления о расписании занятий"
    }
    
    tasks_status = {}
    for task_key in task_names.keys():
        tasks_status[task_key] = get_task_status(task_key)
    
    status_lines = []
    for task_key, task_display_name in task_names.items():
        status = tasks_status[task_key]
        status_icon = "✅" if status else "❌"
        status_lines.append(f"{status_icon} {task_display_name}: {'Вкл.' if status else 'Выкл.'}")
    
    text = (
        f"⚙️ Управление тасками\n\n"
        "Выберите таск для переключения:\n\n" +
        "\n".join(status_lines)
    )
    
    await message.edit_text(text=text, reply_markup=get_admin_tasks_keyboard())


@router.callback_query(F.data == "admin_tasks")
@admin_only
@sync_username
async def handle_admin_tasks(callback: types.CallbackQuery):
    """Отображает меню управления тасками."""
    await _update_admin_tasks_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_task:"))
@admin_only
@sync_username
async def handle_toggle_task(callback: types.CallbackQuery):
    """Переключает статус таска."""
    task_key = callback.data.split(":")[1]
    
    task_names = {
        "daily_schedule": "Ежедневная рассылка расписания",
        "birthday_notifications": "Уведомления о днях рождения",
        "new_year_greetings": "Новогодние поздравления",
        "schedule_notifications": "Уведомления о расписании занятий"
    }
    
    task_display_name = task_names.get(task_key, task_key)
    
    # Переключаем таск
    new_status = toggle_task(task_key)
    
    status_text = "включен" if new_status else "выключен"
    await callback.answer(f"Таск '{task_display_name}' {status_text}", show_alert=True)
    
    write_user_log(
        f"Админ {callback.from_user.full_name} ({callback.from_user.id}) "
        f"{'включил' if new_status else 'выключил'} таск '{task_display_name}'"
    )
    
    # Обновляем меню
    await _update_admin_tasks_menu(callback.message)