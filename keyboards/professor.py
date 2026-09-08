from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_select_professor_keyboard(professors_list: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for professor in professors_list:
        builder.button(text=professor, callback_data=f"professor_select_{professor}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="start"))
    return builder.as_markup()

