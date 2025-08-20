from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_back_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])