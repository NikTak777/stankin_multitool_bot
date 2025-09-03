from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_inline_keyboard(
        is_group_admin: bool = False,
        is_bot_admin: bool = False
) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📅 Расписание", callback_data="schedule")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="info")],
        [InlineKeyboardButton(text="🎁 Вишлист друга", callback_data="friend_wishlist")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="help")]
    ]

    if is_group_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="🛠 Панель группы", callback_data="panel")])

    if is_bot_admin:
        keyboard.insert(-1, [InlineKeyboardButton(text="👑 Панель админа", callback_data="admin_panel")]) #🖥

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
