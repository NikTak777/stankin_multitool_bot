# keyboards/admin_panel.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.database_utils.task_management import get_all_tasks_status


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Главная", callback_data="admin_panel"),
        InlineKeyboardButton(text="🏆 Активность", callback_data="activity_panel"),
        InlineKeyboardButton(text="🗓️ Используемость", callback_data="usability_panel"),
    )
    builder.row(InlineKeyboardButton(
        text="⚙️ Управление тасками",
        callback_data="task_panel"
    ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад в меню",
        callback_data="start"
    ))
    return builder.as_markup()


TASK_ICONS = {
    "daily_schedule": "📅",
    "birthday_notifications": "🎂",
    "new_year_greetings": "🎄",
    "schedule_notifications": "⏰"
}


def get_admin_tasks_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления тасками в админ-панели"""
    tasks_status = get_all_tasks_status()

    builder = InlineKeyboardBuilder()

    for task_key, task_icon in TASK_ICONS.items():
        status = tasks_status.get(task_key, True)

        color_button = "success" if status else "danger"

        builder.add(InlineKeyboardButton(
            text=f"{task_icon}",
            callback_data=f"toggle_task:{task_key}",
            style=color_button,
        ))

    builder.adjust(4)

    builder.row(InlineKeyboardButton(
        text="⬅️ Назад в панель админа",
        callback_data="admin_panel"
    ))

    return builder.as_markup()