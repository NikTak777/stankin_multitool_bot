from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_start_inline_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть расписание", callback_data="view_schedule")],
        #[InlineKeyboardButton(text="Указать номер группы", callback_data="set_group")],
        #[InlineKeyboardButton(text="Указать дату дня рождения", callback_data="start_birthdate_input")],
        [InlineKeyboardButton(text="Показать информацию об аккаунте", callback_data="info_account")],
        #[InlineKeyboardButton(text="Указать новый никнейм", callback_data="set_nickname")],
        #[InlineKeyboardButton(text="Ввести новый вишлист", callback_data="set_wishlist")],
        [InlineKeyboardButton(text="Посмотреть вишлист друга", callback_data="view_friend_wishlist")],
        [InlineKeyboardButton(text="Редактировать профиль", callback_data="edit_profile_menu")]
    ])
    return keyboard
