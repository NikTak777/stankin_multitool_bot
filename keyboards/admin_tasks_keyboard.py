# keyboards/admin_tasks_keyboard.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.database_utils.task_management import get_all_tasks_status


def get_admin_tasks_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления тасками в админ-панели."""
    tasks_status = get_all_tasks_status()
    
    # Названия тасков для отображения
    task_names = {
        "daily_schedule": "📅 Ежедневная рассылка расписания",
        "birthday_notifications": "🎂 Уведомления о днях рождения",
        "new_year_greetings": "🎄 Новогодние поздравления",
        "schedule_notifications": "⏰ Уведомления о расписании занятий"
    }
    
    builder = InlineKeyboardBuilder()
    
    for task_key, task_display_name in task_names.items():
        status = tasks_status.get(task_key, True)
        status_icon = "✅" if status else "❌"
        status_text = "Вкл." if status else "Выкл."
        
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {task_display_name}: {status_text}",
            callback_data=f"toggle_task:{task_key}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад в панель админа",
        callback_data="admin_panel"
    ))
    
    return builder.as_markup()

