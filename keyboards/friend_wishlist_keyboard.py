from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_error_wishlist_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заново", callback_data="friend_wishlist")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
    ])