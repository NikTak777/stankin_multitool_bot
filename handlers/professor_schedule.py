from datetime import datetime, timedelta
from typing import Optional

import pytz
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from decorators.ensure_user_in_db import ensure_user_in_db
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from keyboards.back_to_menu import get_back_inline_keyboard
from keyboards.schedule_keyboards import get_professor_week_days_keyboard
from services.professor_schedule_service import (
    fetch_professor_schedule_for_day,
    format_professor_schedule_day,
    sanitize_professor_slug,
)
from states.schedule import ScheduleState
from utils.database import get_user_info, update_last_professor_fio
from utils.logger import write_user_log

router = Router()
tz_moscow = pytz.timezone("Europe/Moscow")

_PROFESSOR_FIO_PROMPT = (
    "👨‍🏫 Введите <b>ФИО преподавателя</b> так, как оно указано в расписании "
    "(например <code>Иванов И.И</code>)."
)

_ERR_MESSAGES = {
    "not_found": "❌ Преподаватель не найден. Попробуйте ввести ФИО ещё раз.",
    "connection": "⚠️ Не удалось связаться с сервером расписания. Попробуйте позже.",
    "http_error": "⚠️ Сервер расписания вернул ошибку. Попробуйте позже.",
    "bad_json": "⚠️ Некорректный ответ сервера расписания.",
    "timeout": "⚠️ Сервер расписания не ответил вовремя. Попробуйте позже.",
}


def _professor_error_reply_markup(error_key: str) -> InlineKeyboardMarkup:
    """Для not_found — кнопка повторного ввода ФИО (колбек professor_schedule)."""
    if error_key == "not_found":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад в меню",
                        callback_data="start",
                    ),
                    InlineKeyboardButton(
                        text="🔄 Заново",
                        callback_data="professor_schedule",
                    ),
                ],
            ]
        )
    return get_back_inline_keyboard("start")


def _skip_sunday(dt: datetime) -> datetime:
    while dt.weekday() == 6:
        dt += timedelta(days=1)
    return dt


def _professor_keyboard_start_for_target(target_date: datetime) -> datetime:
    """
    Старт клавиатуры для кастомной даты:
    тот же день недели, что и "сегодня", но в неделе выбранной даты.
    """
    today_weekday = datetime.now(tz=tz_moscow).weekday()
    shift_back = (target_date.weekday() - today_weekday) % 7
    return target_date - timedelta(days=shift_back)


def _parse_prof_schedule_offset_callback(data: str) -> tuple[int, datetime, datetime]:
    """prof_schedule_offset_{offset}_{week}_{anchor}"""
    prefix = "prof_schedule_offset_"
    if not data.startswith(prefix):
        raise ValueError(f"Bad prof offset callback: {data}")
    rest = data[len(prefix) :]
    off_str, week_s, anchor_s = rest.split("_", 2)
    offset = int(off_str)
    week_start = datetime.strptime(week_s, "%Y-%m-%d").replace(tzinfo=tz_moscow)
    anchor_day = datetime.strptime(anchor_s, "%Y-%m-%d").date()
    anchor_dt = datetime.combine(anchor_day, datetime.min.time()).replace(tzinfo=tz_moscow)
    return offset, week_start, anchor_dt


def _parse_prof_schedule_week_callback(data: str) -> tuple[datetime, datetime]:
    """prof_schedule_week_{week}_{anchor}"""
    prefix = "prof_schedule_week_"
    if not data.startswith(prefix):
        raise ValueError(f"Bad prof week callback: {data}")
    rest = data[len(prefix) :]
    week_s, anchor_s = rest.split("_", 1)
    week_start = datetime.strptime(week_s, "%Y-%m-%d").replace(tzinfo=tz_moscow)
    anchor_day = datetime.strptime(anchor_s, "%Y-%m-%d").date()
    anchor_dt = datetime.combine(anchor_day, datetime.min.time()).replace(tzinfo=tz_moscow)
    return week_start, anchor_dt


async def _show_professor_schedule_for_date(
    *,
    professor_slug: str,
    professor_display: str,
    target_date: datetime,
    keyboard_start: datetime,
    callback: types.CallbackQuery | None = None,
    message: types.Message | None = None,
    state: FSMContext | None = None,
    user_id: Optional[int] = None,
):
    """Показать расписание преподавателя с недельной клавиатурой."""
    error_key, lessons = await fetch_professor_schedule_for_day(
        professor_slug, target_date.day, target_date.month
    )

    markup = get_professor_week_days_keyboard(
        start_date=keyboard_start,
        selected_date=target_date,
    )

    if error_key == "not_found":
        text = _ERR_MESSAGES["not_found"]
        if state:
            await state.clear()
        if user_id is not None:
            update_last_professor_fio(user_id, None)
    elif error_key:
        text = _ERR_MESSAGES.get(error_key, _ERR_MESSAGES["http_error"])
    else:
        text = format_professor_schedule_day(
            lessons, target_date.day, target_date.month, professor_display
        )

    try:
        if callback:
            if error_key:
                await callback.message.edit_text(
                    text,
                    reply_markup=_professor_error_reply_markup(error_key),
                )
            else:
                await callback.message.edit_text(
                    text,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
            await callback.answer()
        elif message:
            if error_key:
                await message.answer(
                    text,
                    reply_markup=_professor_error_reply_markup(error_key),
                )
            else:
                await message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=markup,
                )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data == "professor_schedule_open")
@private_only
@ensure_user_in_db
@sync_username
async def professor_schedule_open_from_menu(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    """Из главного меню: если в БД есть ФИО — сразу показать; иначе запросить."""
    await state.clear()
    uid = callback.from_user.id
    info = get_user_info(uid)
    saved = (info or {}).get("last_professor_fio")

    if saved and str(saved).strip():
        fio_clean = str(saved).strip()
        slug = sanitize_professor_slug(fio_clean)
        today = datetime.now(tz=tz_moscow)
        error_key, lessons = await fetch_professor_schedule_for_day(slug, today.day, today.month)

        if error_key == "not_found":
            update_last_professor_fio(uid, None)
            await state.set_state(ScheduleState.entering_professor_name)
            await callback.message.edit_text(
                "Сохранённый преподаватель не найден в расписании.\n\n" + _PROFESSOR_FIO_PROMPT,
                parse_mode="HTML",
                reply_markup=get_back_inline_keyboard("start"),
            )
            await callback.answer()
            return

        if error_key:
            await callback.answer(
                _ERR_MESSAGES.get(error_key, _ERR_MESSAGES["http_error"]),
                show_alert=True,
            )
            return

        await state.set_state(ScheduleState.viewing_professor_schedule)
        await state.update_data(professor_slug=slug, professor_display=fio_clean)

        body = format_professor_schedule_day(lessons, today.day, today.month, fio_clean)
        await callback.message.edit_text(
            body,
            parse_mode="HTML",
            reply_markup=get_professor_week_days_keyboard(
                start_date=today,
                selected_date=today,
            ),
        )
        await callback.answer()
        write_user_log(
            f"Пользователь {callback.from_user.full_name} ({uid}) открыл сохранённое "
            f"расписание преподавателя '{slug}'"
        )
        return

    await state.set_state(ScheduleState.entering_professor_name)
    await callback.message.edit_text(
        _PROFESSOR_FIO_PROMPT,
        parse_mode="HTML",
        reply_markup=get_back_inline_keyboard("start"),
    )
    await callback.answer()


@router.callback_query(F.data == "professor_schedule")
@private_only
@ensure_user_in_db
@sync_username
async def professor_schedule_change_professor(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    """С клавиатуры расписания: сменить преподавателя — ввод нового ФИО."""
    await state.clear()
    await state.set_state(ScheduleState.entering_professor_name)

    await callback.message.edit_text(
        _PROFESSOR_FIO_PROMPT,
        parse_mode="HTML",
        reply_markup=get_back_inline_keyboard("start"),
    )
    await callback.answer()


@router.message(ScheduleState.entering_professor_name, F.text)
@private_only
@ensure_user_in_db
@sync_username
async def professor_schedule_receive_name(message: types.Message, state: FSMContext):
    raw = message.text.strip()
    slug = sanitize_professor_slug(raw)

    if not slug:
        await message.answer(
            "Пожалуйста, введите непустое ФИО текстом или нажмите «Назад в меню».",
            reply_markup=get_back_inline_keyboard("start"),
        )
        return

    today = datetime.now(tz=tz_moscow)
    day, month = today.day, today.month

    error_key, lessons = await fetch_professor_schedule_for_day(slug, day, month)

    if error_key:
        await state.clear()
        msg = _ERR_MESSAGES.get(error_key, _ERR_MESSAGES["http_error"])
        await message.answer(
            msg,
            reply_markup=_professor_error_reply_markup(error_key),
        )
        write_user_log(
            f"Пользователь {message.from_user.full_name} ({message.from_user.id}): "
            f"расписание преподавателя '{slug}' — ошибка {error_key}"
        )
        return

    await state.set_state(ScheduleState.viewing_professor_schedule)
    await state.update_data(professor_slug=slug, professor_display=raw)

    update_last_professor_fio(message.from_user.id, raw)

    body = format_professor_schedule_day(lessons, day, month, raw)
    await message.answer(
        body,
        parse_mode="HTML",
        reply_markup=get_professor_week_days_keyboard(
            start_date=today,
            selected_date=today,
        ),
    )
    write_user_log(
        f"Пользователь {message.from_user.full_name} ({message.from_user.id}) "
        f"запросил расписание преподавателя '{slug}' на сегодня"
    )


@router.callback_query(F.data.startswith("prof_schedule_offset_"))
@sync_username
async def professor_handle_day_offset(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    slug = data.get("professor_slug")
    display = data.get("professor_display")
    if not slug:
        await callback.answer(
            "Сессия истекла. Откройте расписание преподавателя из меню снова.",
            show_alert=True,
        )
        return

    try:
        offset, week_start, anchor_dt = _parse_prof_schedule_offset_callback(callback.data)
    except ValueError:
        await callback.answer("Ошибка кнопки", show_alert=True)
        return

    today = datetime.now(tz=tz_moscow)
    is_stale = anchor_dt.date() != today.date()

    if is_stale:
        target_date = _skip_sunday(today)
        keyboard_start = today
    else:
        target_date = anchor_dt + timedelta(days=offset)
        target_date = _skip_sunday(target_date)
        keyboard_start = week_start

    await _show_professor_schedule_for_date(
        professor_slug=slug,
        professor_display=display or slug,
        target_date=target_date,
        keyboard_start=keyboard_start,
        callback=callback,
        state=state,
        user_id=callback.from_user.id,
    )

    write_user_log(
        f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) "
        f"— расписание преподавателя на {target_date.strftime('%d.%m.%Y')}"
    )


@router.callback_query(F.data.startswith("prof_schedule_week_"))
@sync_username
async def professor_handle_week_switch(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    slug = data.get("professor_slug")
    display = data.get("professor_display")
    if not slug:
        await callback.answer(
            "Сессия истекла. Откройте расписание преподавателя из меню снова.",
            show_alert=True,
        )
        return

    try:
        week_target, anchor_dt = _parse_prof_schedule_week_callback(callback.data)
    except ValueError:
        await callback.answer("Ошибка кнопки", show_alert=True)
        return

    today = datetime.now(tz=tz_moscow)
    is_stale = anchor_dt.date() != today.date()

    if is_stale:
        target_date = _skip_sunday(today)
        keyboard_start = today
    else:
        target_date = week_target
        keyboard_start = week_target

    await _show_professor_schedule_for_date(
        professor_slug=slug,
        professor_display=display or slug,
        target_date=target_date,
        keyboard_start=keyboard_start,
        callback=callback,
        state=state,
        user_id=callback.from_user.id,
    )


@router.callback_query(F.data == "prof_schedule_custom")
@sync_username
async def professor_choose_custom_day(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("professor_slug"):
        await callback.answer(
            "Сессия истекла. Откройте расписание преподавателя из меню снова.",
            show_alert=True,
        )
        return

    buttons = [
        [types.KeyboardButton(text=str(i)) for i in range(j, min(j + 7, 32))]
        for j in range(1, 32, 7)
    ]
    builder = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await callback.message.answer(
        "Выберите день:",
        reply_markup=builder,
    )
    await state.set_state(ScheduleState.professor_choosing_day)
    await callback.answer()


@router.message(ScheduleState.professor_choosing_day, F.text)
@sync_username
async def professor_choose_custom_month(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 31:
        await state.update_data(custom_day=int(message.text))

        month_buttons = [
            [types.KeyboardButton(text=str(i)) for i in range(j, min(j + 4, 13))]
            for j in range(1, 13, 4)
        ]
        builder = types.ReplyKeyboardMarkup(keyboard=month_buttons, resize_keyboard=True)

        await message.answer(
            "Выберите месяц:",
            reply_markup=builder,
        )
        await state.set_state(ScheduleState.professor_choosing_month)
    else:
        await message.answer("Пожалуйста, выберите корректный день (1–31):")


@router.message(ScheduleState.professor_choosing_month, F.text)
@private_only
@ensure_user_in_db
@sync_username
async def professor_show_custom_date(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (1 <= int(message.text) <= 12):
        await message.answer("Пожалуйста, выберите корректный месяц (1–12):")
        return

    month = int(message.text)
    data = await state.get_data()
    day = data["custom_day"]
    slug = data["professor_slug"]
    display = data.get("professor_display") or slug

    year = datetime.now(tz=tz_moscow).year
    try:
        target_date = datetime(year, month, day, tzinfo=tz_moscow)
    except ValueError:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Выбрать другую дату",
                        callback_data="prof_schedule_custom",
                    )
                ]
            ]
        )
        await message.answer(
            "❌ Неверная дата. Проверьте день и месяц.",
            reply_markup=kb,
        )
        await state.set_state(ScheduleState.viewing_professor_schedule)
        return

    tmp_msg = await message.answer("...", reply_markup=types.ReplyKeyboardRemove())
    await tmp_msg.delete()

    await state.set_state(ScheduleState.viewing_professor_schedule)
    await state.update_data(professor_slug=slug, professor_display=display)

    await _show_professor_schedule_for_date(
        professor_slug=slug,
        professor_display=display,
        target_date=target_date,
        keyboard_start=_professor_keyboard_start_for_target(target_date),
        message=message,
        state=state,
        user_id=message.from_user.id,
    )

    write_user_log(
        f"Пользователь {message.from_user.full_name} ({message.from_user.id}) "
        f"— расписание преподавателя на {target_date.strftime('%d.%m.%Y')} (другой день)"
    )