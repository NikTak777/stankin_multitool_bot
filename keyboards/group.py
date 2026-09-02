from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.group import get_available_group_codes

async def get_enter_code_group_keyboard() -> InlineKeyboardMarkup:
    codes = await get_available_group_codes()

    builder = InlineKeyboardBuilder()
    for code in codes['data']:
        builder.button(text=code, callback_data=f"group_code_{code}")
    return builder.as_markup()