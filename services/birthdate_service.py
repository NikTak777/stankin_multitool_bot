from datetime import datetime
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import add_user_with_bd, get_user_info, update_is_approved
from utils.logger import write_user_log
from utils.date_utils import format_date

import pytz

tz_moscow = pytz.timezone("Europe/Moscow")

async def save_user_birthday(user_id: int, username: str, full_name: str, day: int, month: int, year: int, message):
    """
    Логика сохранения дня рождения пользователя + ответное сообщение.
    """
    # Сохраняем в БД
    add_user_with_bd(user_id, username, full_name, day, month, year)

    user_info = get_user_info(user_id)
    if user_info["is_approved"] is None or user_info["is_approved"] == "":
        update_is_approved(user_id, True)

    month_list = [
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
    ]

    now = datetime.now(tz=tz_moscow)
    today_day, today_month = now.day, now.month

    formatted_date = format_date(day, month, year)

    # --- Логика выбора текста ---
    if month == today_month:
        if day == today_day:
            message_to_user = f"🎉 Ух ты, сегодня ваш день рождения! Поздравляю! 🎂\nДата рождения {formatted_date} сохранена."
        elif day > today_day:
            message_to_user = f"✨ У вас скоро день рождения! С наступающим!\nДата {formatted_date} сохранена."
        elif today_day - day <= 14:
            message_to_user = f"🎁 Недавно был день рождения? Поздравляю с прошедшим!\nДата {formatted_date} сохранена."
        else:
            message_to_user = f"Спасибо! Жду с нетерпением следующий {month_list[month - 1]}!\nДата {formatted_date} сохранена."
    else:
        if today_month - month == 1 and day - today_day >= 17:
            message_to_user = f"🎂 Недавно был день рождения? Поздравляю с прошедшим!\nДата {formatted_date} сохранена."
        else:
            message_to_user = f"Спасибо! Жду с нетерпением {month_list[month - 1]}!\nДата {formatted_date} сохранена."

    # Отправляем сообщение пользователю
    await message.answer(message_to_user, reply_markup=ReplyKeyboardRemove())

    # Проверяем, есть ли у пользователя группа
    user_group, user_subgroup = user_info["user_group"], user_info["user_subgroup"]
    if not user_group or not user_subgroup:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📌 Указать номер группы", callback_data="ask_group")],
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_group")]
        ])
        await message.answer("Хотите указать номер вашей группы?", reply_markup=keyboard)

    # Лог
    msg = f"Пользователь {full_name} ({user_id}) установил дату рождения {day}.{month}.{year}"
    write_user_log(msg)
