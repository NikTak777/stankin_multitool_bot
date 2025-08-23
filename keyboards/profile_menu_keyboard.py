from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_menu_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile_menu")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    return keyboard