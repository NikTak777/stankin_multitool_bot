from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.time import get_now_time
from services.contest import START_DATE, END_DATE

def get_admin_contest_menu_keyboard()  -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Запустить розыгрыш", callback_data="start-raffle", style="danger")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contest_info_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")],
    ]

    if START_DATE <= get_now_time() <= END_DATE:
        keyboard.insert(-1, [InlineKeyboardButton(text="Условия розыгрыша", callback_data="contest_rules")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_contest_rules_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Назад к статистике", callback_data="contest")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)