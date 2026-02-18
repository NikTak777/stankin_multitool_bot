from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import get_schedule_notifications_status

def get_edit_profile_inline_keyboard(user_id: int):
    """Создает клавиатуру редактирования профиля с текущим статусом рассылки расписания"""
    status = "✅" if get_schedule_notifications_status(user_id) else "❌"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Номер группы", callback_data="group")],
        [InlineKeyboardButton(text="🎂 День рождения", callback_data="start_birthdate_input")],
        [InlineKeyboardButton(text="👤 Никнейм", callback_data="nickname")],
        [InlineKeyboardButton(text="🎁 Вишлист", callback_data="my_wishlist")],
        [InlineKeyboardButton(text=f"{status} Рассылка расписания", callback_data="toggle_schedule_notifications")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="info")]
    ])
    return keyboard