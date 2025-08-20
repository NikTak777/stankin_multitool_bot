from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_edit_profile_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Указать номер группы", callback_data="set_group")],
        [InlineKeyboardButton(text="Указать дату дня рождения", callback_data="start_birthdate_input")],
        [InlineKeyboardButton(text="Указать новый никнейм", callback_data="set_nickname")],
        [InlineKeyboardButton(text="Ввести новый вишлист", callback_data="set_wishlist")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="start")]
    ])
    return keyboard