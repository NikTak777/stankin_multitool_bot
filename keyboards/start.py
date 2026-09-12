from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.contest import is_contest_now

def get_start_inline_keyboard(
        is_group_admin: bool = False,
        is_bot_admin: bool = False
) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📅 Расписание", callback_data="schedule")],
        [InlineKeyboardButton(text="👨‍🏫 Расписание преподавателя", callback_data="professor_schedule_open")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="info")],
        [InlineKeyboardButton(text="🤝 Друзья", callback_data="friends_menu")],
        [InlineKeyboardButton(text="🔎 Поиск людей", callback_data="search_profile")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="help")]
    ]

    if is_contest_now():
        keyboard.insert(0, [InlineKeyboardButton(text="🎁 Розыгрыш Telegram Premium", callback_data="contest", style="primary")])
    else:
        keyboard.insert(2, [InlineKeyboardButton(text="🎁 Розыгрыш Telegram Premium", callback_data="contest", style="primary")])

    if is_group_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="🛠 Панель группы", callback_data="panel")])

    if is_bot_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="👑 Панель админа", callback_data="admin_panel")])

    if is_bot_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="🎲 Панель розыгрыша", callback_data="contest-panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
