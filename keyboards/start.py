from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_inline_keyboard(
        is_group_admin: bool = False,
        is_bot_admin: bool = False
) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📅 Расписание", callback_data="schedule")],
        [InlineKeyboardButton(text="👨‍🏫 Расписание преподавателя", callback_data="professor_schedule_open")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="info")],
        [InlineKeyboardButton(text="🤝 Друзья", callback_data="friends_menu")],
        [InlineKeyboardButton(text="🔎 Чужой профиль", callback_data="other_profile")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="help")]
    ]

    if is_group_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="🛠 Панель группы", callback_data="panel")])

    if is_bot_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="👑 Панель админа", callback_data="admin_panel")]) #🖥

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
