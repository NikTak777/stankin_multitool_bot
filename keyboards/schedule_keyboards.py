from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import pytz

tz_moscow = pytz.timezone("Europe/Moscow")

def get_day_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Сегодня", callback_data="schedule_today")
    builder.button(text="Завтра", callback_data="schedule_tomorrow")
    builder.button(text="Выбрать день", callback_data="schedule_custom")
    builder.adjust(1)
    return builder.as_markup()


def get_week_days_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с 6 днями недели, пропуская воскресенье."""
    builder = InlineKeyboardBuilder()
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    today = datetime.now(tz=tz_moscow)
    day_date = today
    count = 0

    while count < 6:
        if day_date.weekday() == 6:  # пропуск воскресенья
            day_date += timedelta(days=1)
            continue

        text_on_button = f"{day_names[day_date.weekday()]} ({day_date.day:02}.{day_date.month:02})"
        offset = (day_date.date() - today.date()).days

        builder.button(text=text_on_button, callback_data=f"schedule_offset_{offset}")
        day_date += timedelta(days=1)
        count += 1

    builder.button(text="🔀 Другой день", callback_data="schedule_custom")
    builder.adjust(3, 3, 1)
    return builder.as_markup()
