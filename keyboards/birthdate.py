# keyboards/birthdate.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_birthdate_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Указать дату дня рождения", callback_data="start_birthdate_input")]
    ])
    return keyboard