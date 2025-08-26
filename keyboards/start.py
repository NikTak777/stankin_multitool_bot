from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_inline_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📅 Расписание", callback_data="schedule")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="info")],
        [InlineKeyboardButton(text="🎁 Вишлист друга", callback_data="friend_wishlist")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="help")]
    ]

    if is_admin:
        # Вставляем кнопку перед FAQ
        keyboard.insert(-1, [InlineKeyboardButton(text="🛠 Панель группы", callback_data="panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
