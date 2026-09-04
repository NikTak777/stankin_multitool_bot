from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.group import get_available_group_codes, get_available_group_years, get_available_group_names

async def get_enter_code_group_keyboard(callback_target: str = "edit_profile_menu") -> InlineKeyboardMarkup:
    codes = await get_available_group_codes()

    builder = InlineKeyboardBuilder()
    for code in codes['data']:
        builder.button(text=code, callback_data=f"group_code_{code}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=callback_target))
    return builder.as_markup()


async def get_select_year_group_keyboard(
        user_group_code: str,
        callback_target: str = "edit_profile_menu"
) -> InlineKeyboardMarkup:
    years = await get_available_group_years(user_group_code)

    builder = InlineKeyboardBuilder()
    for year in years['data']:
        builder.button(text=year, callback_data=f"group_year_{year}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=callback_target))
    return builder.as_markup()


async def get_select_name_group_keyboard(
        user_group_code: str,
        user_group_year: str,
        callback_target: str = "edit_profile_menu"
) -> InlineKeyboardMarkup:
    groups = await get_available_group_names(user_group_code, user_group_year)

    builder = InlineKeyboardBuilder()
    for group in groups['data']:
        builder.button(text=group, callback_data=f"group_name_{group}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data=callback_target))
    return builder.as_markup()


async def get_select_subgroup_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="А", callback_data="subgroup_a"),
            InlineKeyboardButton(text="Б", callback_data="subgroup_b")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)