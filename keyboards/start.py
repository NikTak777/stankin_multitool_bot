from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть расписание", callback_data="view_schedule")],
        [InlineKeyboardButton(text="Показать информацию об аккаунте", callback_data="info")],
        [InlineKeyboardButton(text="Посмотреть вишлист друга", callback_data="friend_wishlist")],
        [InlineKeyboardButton(text="Редактировать профиль >>>", callback_data="edit_profile_menu")]
    ])
    return keyboard
