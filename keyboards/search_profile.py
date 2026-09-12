from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_search_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заново", callback_data="search_profile")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
    ])