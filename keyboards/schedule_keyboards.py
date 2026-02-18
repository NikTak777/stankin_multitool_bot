from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from datetime import datetime, timedelta
import pytz

tz_moscow = pytz.timezone("Europe/Moscow")


def get_week_days_keyboard(start_date: datetime | None = None,
                           friend_id: int | None = None
    ) -> InlineKeyboardMarkup:
    """Создает клавиатуру с 6 днями недели, пропуская воскресенье, начиная от заданной даты."""
    builder = InlineKeyboardBuilder()
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    today = datetime.now(tz=tz_moscow)

    # Если start_date не задана, начинаем с текущей даты
    if start_date is None:
        start_date = today

    day_date = start_date
    count = 0

    # Кнопки дней недели
    while count < 6:
        if day_date.weekday() == 6:  # пропускаем воскресенье
            day_date += timedelta(days=1)
            continue

        text_on_button = f"{day_names[day_date.weekday()]} ({day_date.day:02}.{day_date.month:02})"
        offset = (day_date.date() - today.date()).days

        if friend_id:
            cb = f"schedule_offset_{offset}_{start_date.strftime('%Y-%m-%d')}_f{friend_id}"
        else:
            cb = f"schedule_offset_{offset}_{start_date.strftime('%Y-%m-%d')}"

        builder.button(text=text_on_button, callback_data=cb)
        day_date += timedelta(days=1)
        count += 1

    # Кнопки смены недели
    prev_week = start_date - timedelta(weeks=1)
    next_week = start_date + timedelta(weeks=1)

    if friend_id:
        prev_cb = f"schedule_week_{prev_week.strftime('%Y-%m-%d')}_f{friend_id}"
        next_cb = f"schedule_week_{next_week.strftime('%Y-%m-%d')}_f{friend_id}"
    else:
        prev_cb = f"schedule_week_{prev_week.strftime('%Y-%m-%d')}"
        next_cb = f"schedule_week_{next_week.strftime('%Y-%m-%d')}"

    builder.button(text="◀️ Назад", callback_data=prev_cb)
    builder.button(text="▶️ Вперёд", callback_data=next_cb)

    # Доп. кнопки
    builder.button(text="🔀 Другой день", callback_data="schedule_custom")
    builder.button(text="👥 Чужая группа", callback_data="other_group")

    if friend_id:
        builder.button(text="⬅️ Назад в меню", callback_data="friends_edit_menu")
    else:
        builder.button(text="⬅️ Назад в меню", callback_data="start")

    builder.adjust(3, 3, 2, 2, 1)
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


def get_other_group_schedule_keyboard(target_date: datetime) -> InlineKeyboardMarkup:

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"schedule_other_date_{(target_date - timedelta(days=1)).strftime('%Y-%m-%d')}"
            ),
            InlineKeyboardButton(
                text="▶️ Вперёд",
                callback_data=f"schedule_other_date_{(target_date + timedelta(days=1)).strftime('%Y-%m-%d')}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад в меню",
                callback_data="start"
            )
        ]
    ])
    return kb
