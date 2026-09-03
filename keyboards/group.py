from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.group import get_available_group_codes, get_available_group_years

async def get_enter_code_group_keyboard() -> InlineKeyboardMarkup:
    codes = await get_available_group_codes()

    builder = InlineKeyboardBuilder()
    for code in codes['data']:
        builder.button(text=code, callback_data=f"group_code_{code}")
    builder.adjust(3)
    return builder.as_markup()


async def get_select_year_group_keyboard(user_group_code: str) -> InlineKeyboardMarkup:
    years = await get_available_group_years(user_group_code)

    builder = InlineKeyboardBuilder()
    for year in years['data']:
        builder.button(text=year, callback_data=f"group_year_{year}")
    builder.adjust(3)
    return builder.as_markup()