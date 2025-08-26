from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cancel_inline_keyboard(callback_target: str = "edit_profile_menu") -> InlineKeyboardMarkup:
    """
    Универсальная инлайн-клавиатура с кнопкой ❌ Отмена.
    callback_target — куда возвращаться при нажатии (по умолчанию edit_profile_menu).
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=callback_target)]
        ]
    )
    return keyboard