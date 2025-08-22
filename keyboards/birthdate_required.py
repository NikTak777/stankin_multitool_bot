from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_birthdate_required_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Указать дату дня рождения", callback_data="start_birthdate_input")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])