from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Расписание", callback_data="schedule")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="info")],
        [InlineKeyboardButton(text="🎁 Вишлист друга", callback_data="friend_wishlist")],
        # [InlineKeyboardButton(text="Ред. профиль ➡️", callback_data="edit_profile_menu")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="help")]
    ])
    return keyboard
