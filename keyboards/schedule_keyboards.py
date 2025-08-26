from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz

tz_moscow = pytz.timezone("Europe/Moscow")


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
    builder.button(text="⬅️ Назад в меню", callback_data="start")
    builder.adjust(3, 3, 1)
    return builder.as_markup()


def get_custom_schedule_keyboard(target_date: datetime) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру для кастомного расписания с:
    - Стрелки Вперёд/Назад
    - Кнопка "Выбрать другую дату"
    - Кнопка "Назад в меню"
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [  # ряд 1: листание дней
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"schedule_date_{(target_date - timedelta(days=1)).strftime('%Y-%m-%d')}"
            ),
            InlineKeyboardButton(
                text="▶️ Вперёд",
                callback_data=f"schedule_date_{(target_date + timedelta(days=1)).strftime('%Y-%m-%d')}"
            )
        ],
        [  # ряд 2: выбор другой даты
            InlineKeyboardButton(
                text="🔄 Выбрать другую дату",
                callback_data="schedule_custom"
            )
        ],
        [  # ряд 3: возврат в меню
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data="start"
            )
        ]
    ])
    return kb