from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from datetime import date, datetime, timedelta
import pytz

tz_moscow = pytz.timezone("Europe/Moscow")


def get_week_days_keyboard(start_date: datetime | None = None,
                           friend_id: int | None = None,
                           selected_date: datetime | None = None,
    ) -> InlineKeyboardMarkup:
    """Создает клавиатуру с 6 днями недели, пропуская воскресенье, начиная от заданной даты."""
    builder = InlineKeyboardBuilder()
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    today = datetime.now(tz=tz_moscow) # - timedelta(days=4)  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Календарный день, относительно которого считаются offset в callback
    anchor_day = today.date() 

    # Если start_date не задана, начинаем с текущей даты
    if start_date is None:
        start_date = today

    week_token = start_date.strftime("%Y-%m-%d")
    anchor_token = anchor_day.strftime("%Y-%m-%d")

    day_date = start_date
    count = 0

    # Кнопки дней недели
    while count < 6:
        if day_date.weekday() == 6:  # пропускаем воскресенье
            day_date += timedelta(days=1)
            continue

        text_on_button = f"{day_names[day_date.weekday()]} ({day_date.day:02}.{day_date.month:02})"
        offset = (day_date.date() - anchor_day).days
        if friend_id:
            cb = f"schedule_offset_{offset}_{week_token}_{anchor_token}_f{friend_id}"
        else:
            cb = f"schedule_offset_{offset}_{week_token}_{anchor_token}"

        if selected_date is not None and day_date.date() == selected_date.date():
            builder.button(text=text_on_button, callback_data=cb, style="success")
        else:
            builder.button(text=text_on_button, callback_data=cb)
        day_date += timedelta(days=1)
        count += 1

    # Кнопки смены недели
    prev_week = start_date - timedelta(weeks=1)
    next_week = start_date + timedelta(weeks=1)

    if friend_id:
        prev_cb = f"schedule_week_{prev_week.strftime('%Y-%m-%d')}_{anchor_token}_f{friend_id}"
        next_cb = f"schedule_week_{next_week.strftime('%Y-%m-%d')}_{anchor_token}_f{friend_id}"
    else:
        prev_cb = f"schedule_week_{prev_week.strftime('%Y-%m-%d')}_{anchor_token}"
        next_cb = f"schedule_week_{next_week.strftime('%Y-%m-%d')}_{anchor_token}"

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


def get_professor_week_days_keyboard(
    start_date: datetime | None = None,
    selected_date: datetime | None = None,
) -> InlineKeyboardMarkup:
    """
    Недельная клавиатура для расписания преподавателя (аналог get_week_days_keyboard).
    Колбеки с префиксом prof_schedule_, чтобы не пересекаться с расписанием группы.
    «Чужая группа» заменена на «Другой преподаватель».
    """
    builder = InlineKeyboardBuilder()
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    today = datetime.now(tz=tz_moscow)
    anchor_day = today.date()

    if start_date is None:
        start_date = today

    week_token = start_date.strftime("%Y-%m-%d")
    anchor_token = anchor_day.strftime("%Y-%m-%d")

    day_date = start_date
    count = 0

    while count < 6:
        if day_date.weekday() == 6:
            day_date += timedelta(days=1)
            continue

        text_on_button = f"{day_names[day_date.weekday()]} ({day_date.day:02}.{day_date.month:02})"
        offset = (day_date.date() - anchor_day).days
        cb = f"prof_schedule_offset_{offset}_{week_token}_{anchor_token}"

        if selected_date is not None and day_date.date() == selected_date.date():
            builder.button(text=text_on_button, callback_data=cb, style="success")
        else:
            builder.button(text=text_on_button, callback_data=cb)
        day_date += timedelta(days=1)
        count += 1

    prev_week = start_date - timedelta(weeks=1)
    next_week = start_date + timedelta(weeks=1)

    prev_cb = f"prof_schedule_week_{prev_week.strftime('%Y-%m-%d')}_{anchor_token}"
    next_cb = f"prof_schedule_week_{next_week.strftime('%Y-%m-%d')}_{anchor_token}"

    builder.button(text="◀️ Назад", callback_data=prev_cb)
    builder.button(text="▶️ Вперёд", callback_data=next_cb)

    builder.button(text="🔀 Другой день", callback_data="prof_schedule_custom")
    builder.button(text="👨‍🏫 Другой преподаватель", callback_data="professor_schedule")

    builder.button(text="⬅️ Назад в меню", callback_data="start")

    builder.adjust(3, 3, 2, 2, 1)
    return builder.as_markup()


def get_other_group_schedule_keyboard(
    start_date: datetime | None = None,
    selected_date: datetime | None = None,
) -> InlineKeyboardMarkup:
    """Недельная клавиатура для режима расписания чужой группы."""
    builder = InlineKeyboardBuilder()
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    today = datetime.now(tz=tz_moscow)
    anchor_day = today.date()

    if start_date is None:
        start_date = today

    week_token = start_date.strftime("%Y-%m-%d")
    anchor_token = anchor_day.strftime("%Y-%m-%d")

    day_date = start_date
    count = 0

    while count < 6:
        if day_date.weekday() == 6:
            day_date += timedelta(days=1)
            continue

        text_on_button = f"{day_names[day_date.weekday()]} ({day_date.day:02}.{day_date.month:02})"
        offset = (day_date.date() - anchor_day).days
        cb = f"schedule_other_offset_{offset}_{week_token}_{anchor_token}"

        if selected_date is not None and day_date.date() == selected_date.date():
            builder.button(text=text_on_button, callback_data=cb, style="success")
        else:
            builder.button(text=text_on_button, callback_data=cb)

        day_date += timedelta(days=1)
        count += 1

    prev_week = start_date - timedelta(weeks=1)
    next_week = start_date + timedelta(weeks=1)
    builder.button(
        text="◀️ Назад",
        callback_data=f"schedule_other_week_{prev_week.strftime('%Y-%m-%d')}_{anchor_token}",
    )
    builder.button(
        text="▶️ Вперёд",
        callback_data=f"schedule_other_week_{next_week.strftime('%Y-%m-%d')}_{anchor_token}",
    )

    builder.button(text="🔀 Другой день", callback_data="schedule_other_custom")
    builder.button(text="👥 Другая группа", callback_data="other_group")
    builder.button(text="⬅️ Назад в меню", callback_data="start")

    builder.adjust(3, 3, 2, 2, 1)
    return builder.as_markup()
