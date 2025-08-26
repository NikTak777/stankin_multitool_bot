from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_edit_profile_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Номер группы", callback_data="group")],
        [InlineKeyboardButton(text="🎂 День рождения", callback_data="start_birthdate_input")],
        [InlineKeyboardButton(text="👤 Никнейм", callback_data="nickname")],
        [InlineKeyboardButton(text="🎁 Вишлист", callback_data="my_wishlist")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="info")]
    ])
    return keyboard