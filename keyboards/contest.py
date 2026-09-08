from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_contest_menu_keyboard()  -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="Запустить розыгрыш", callback_data="start-raffle", style="danger")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)