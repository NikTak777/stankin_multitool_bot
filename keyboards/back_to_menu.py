from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_inline_keyboard(callback_target: str = "start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=callback_target)]
    ])