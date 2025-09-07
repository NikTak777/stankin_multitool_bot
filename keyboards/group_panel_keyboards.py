# keyboards/group_panel_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

ALLOWED_HOURS = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6]  # окно 18:00–06:00


def _fmt_hour(h: int) -> str:
    return f"{h:02d}:00"


def get_edit_send_time_keyboard(hour: int) -> types.InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        types.InlineKeyboardButton(text="◀️", callback_data="send_time_left"),
        types.InlineKeyboardButton(text=f"🕗 {_fmt_hour(hour)}", callback_data="noop"),
        types.InlineKeyboardButton(text="▶️", callback_data="send_time_right"),
    )
    b.row(types.InlineKeyboardButton(text="💾 Сохранить", callback_data="send_time_save"))
    b.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="panel"))
    return b.as_markup()
