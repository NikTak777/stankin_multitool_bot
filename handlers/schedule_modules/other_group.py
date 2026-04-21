from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from datetime import datetime, timedelta

import pytz

from states.other_group_schedule import OtherGroupState

from keyboards.cancel_keyboard import get_cancel_inline_keyboard
from keyboards.schedule_keyboards import get_other_group_schedule_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard

from services.schedule_service import format_schedule, load_schedule

from utils.logger import write_user_log
from utils.group_utils import is_valid_group_name

from filters.require_fsm import RequireFSM

router = Router()

tz_moscow = pytz.timezone("Europe/Moscow")


def _skip_sunday(dt: datetime) -> datetime:
    while dt.weekday() == 6:
        dt += timedelta(days=1)
    return dt


def _parse_other_offset_callback(data: str) -> tuple[int, datetime, datetime | None]:
    """
    Новый формат: schedule_other_offset_{offset}_{week}_{anchor}
    Старый формат: schedule_other_offset_{offset}_{week}
    """
    parts = data.split("_")
    if len(parts) < 5:
        raise ValueError(f"Bad schedule_other_offset callback: {data}")

    offset = int(parts[3])
    week_start = datetime.strptime(parts[4], "%Y-%m-%d").replace(tzinfo=tz_moscow)
    anchor_dt = None
    if len(parts) >= 6:
        anchor_day = datetime.strptime(parts[5], "%Y-%m-%d").date()
        anchor_dt = datetime.combine(anchor_day, datetime.min.time()).replace(tzinfo=tz_moscow)
    return offset, week_start, anchor_dt


def _parse_other_week_callback(data: str) -> tuple[datetime, datetime | None]:
    """
    Новый формат: schedule_other_week_{week}_{anchor}
    Старый формат: schedule_other_week_{week}
    """
    parts = data.split("_")
    if len(parts) < 4:
        raise ValueError(f"Bad schedule_other_week callback: {data}")

    week_start = datetime.strptime(parts[3], "%Y-%m-%d").replace(tzinfo=tz_moscow)
    anchor_dt = None
    if len(parts) >= 5:
        anchor_day = datetime.strptime(parts[4], "%Y-%m-%d").date()
        anchor_dt = datetime.combine(anchor_day, datetime.min.time()).replace(tzinfo=tz_moscow)
    return week_start, anchor_dt


def _other_keyboard_start_for_target(target_date: datetime) -> datetime:
    """Тот же день недели, что и сегодня, в неделе выбранной даты."""
    today_weekday = datetime.now(tz=tz_moscow).weekday()
    shift_back = (target_date.weekday() - today_weekday) % 7
    return target_date - timedelta(days=shift_back)


@router.callback_query(F.data == "other_group")
async def choose_other_group_schedule(callback: CallbackQuery, state: FSMContext):
    """Запросить у пользователя ввод номер другой группы"""
    write_user_log(f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку ввода другой группы")
    await callback.answer()
    await callback.message.edit_text(
        text="Введите номер группы, расписание которой хотите посмотреть (например, ИДБ-23-10):",
        reply_markup=get_cancel_inline_keyboard("schedule")
    )
    await state.set_state(OtherGroupState.waiting_for_group)


@router.message(StateFilter(OtherGroupState.waiting_for_group))
async def process_group_input(message: Message, state: FSMContext):
    """Проверить введённое имя группы и показать расписание"""

    other_name = message.text.strip()

    if not is_valid_group_name(other_name):
        await message.answer("⚠️ Номер группы некорректный! Введите в формате XXX-00-00 (например, ИДБ-23-10):")
        return

    await state.update_data(group_name=other_name)

    today = datetime.now(tz=tz_moscow)

    await show_other_schedule_for_date(
        user_id=message.from_user.id,
        user_fullname=message.from_user.full_name,
        group_name=other_name,
        target_date=today,
        message=message
    )


@router.callback_query(F.data.startswith("schedule_other_offset_"), RequireFSM("group_name"))
async def handle_other_schedule_offset(callback: CallbackQuery, state: FSMContext):
    """Выбор дня недели для чужой группы."""
    offset, week_start, anchor_dt = _parse_other_offset_callback(callback.data)
    data = await state.get_data()
    group_name = data.get("group_name")

    today = datetime.now(tz_moscow)
    is_stale = anchor_dt is None or anchor_dt.date() != today.date()

    if is_stale:
        target_date = _skip_sunday(today)
        keyboard_start = today
    else:
        base = anchor_dt if anchor_dt is not None else today
        target_date = _skip_sunday(base + timedelta(days=offset))
        keyboard_start = week_start

    await show_other_schedule_for_date(
        user_id=callback.from_user.id,
        user_fullname=callback.from_user.full_name,
        group_name=group_name,
        target_date=target_date,
        keyboard_start=keyboard_start,
        callback=callback
    )


@router.callback_query(F.data.startswith("schedule_other_week_"), RequireFSM("group_name"))
async def handle_other_schedule_week(callback: CallbackQuery, state: FSMContext):
    """Листание недель для чужой группы."""
    week_target, anchor_dt = _parse_other_week_callback(callback.data)
    data = await state.get_data()
    group_name = data.get("group_name")

    today = datetime.now(tz_moscow)
    is_stale = anchor_dt is None or anchor_dt.date() != today.date()
    target_date = _skip_sunday(today) if is_stale else week_target
    keyboard_start = today if is_stale else week_target

    await show_other_schedule_for_date(
        user_id=callback.from_user.id,
        user_fullname=callback.from_user.full_name,
        group_name=group_name,
        target_date=target_date,
        keyboard_start=keyboard_start,
        callback=callback
    )


@router.callback_query(F.data == "schedule_other_custom", RequireFSM("group_name"))
async def choose_other_custom_day(callback: CallbackQuery, state: FSMContext):
    # UX как у обычного расписания: reply-клавиатура выбора дня/месяца.
    from aiogram import types
    builder = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=str(i)) for i in range(j, min(j + 7, 32))] for j in range(1, 32, 7)],
        resize_keyboard=True
    )
    await callback.message.answer("Выберите день:", reply_markup=builder)
    await state.set_state(OtherGroupState.choosing_day)
    await callback.answer()


@router.message(StateFilter(OtherGroupState.choosing_day))
async def choose_other_custom_month(message: Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 31:
        await state.update_data(day=int(message.text))
        from aiogram import types
        builder = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=str(i)) for i in range(j, min(j + 4, 13))] for j in range(1, 13, 4)],
            resize_keyboard=True
        )
        await message.answer("Выберите месяц:", reply_markup=builder)
        await state.set_state(OtherGroupState.choosing_month)
    else:
        await message.answer("Пожалуйста, выберите корректный день (1–31):")


@router.message(StateFilter(OtherGroupState.choosing_month))
async def show_other_custom_schedule(message: Message, state: FSMContext):
    if not (message.text.isdigit() and 1 <= int(message.text) <= 12):
        await message.answer("Пожалуйста, выберите корректный месяц (1–12):")
        return

    await state.update_data(month=int(message.text))
    data = await state.get_data()
    day, month = data["day"], data["month"]
    group_name = data.get("group_name")

    target_date = datetime(datetime.now(tz_moscow).year, month, day, tzinfo=tz_moscow)
    kb_start = _other_keyboard_start_for_target(target_date)

    from aiogram import types
    tmp_msg = await message.answer("...", reply_markup=types.ReplyKeyboardRemove())
    await tmp_msg.delete()

    await state.set_state(OtherGroupState.waiting_for_group)
    await show_other_schedule_for_date(
        user_id=message.from_user.id,
        user_fullname=message.from_user.full_name,
        group_name=group_name,
        target_date=target_date,
        keyboard_start=kb_start,
        message=message
    )


@router.callback_query(F.data.startswith("schedule_other_date_"))
async def handle_other_schedule_date_fallback(callback: CallbackQuery, state: FSMContext):
    await choose_other_group_schedule(callback, state)


async def show_other_schedule_for_date(
        user_id: int, user_fullname: str, group_name: str, target_date: datetime,
        keyboard_start: datetime | None = None,
        message: Message | None = None,
        callback: CallbackQuery | None = None,
):
    """Отображает расписание другой группы на выбранную дату"""
    try:
        data = load_schedule(group_name + ".json")
        schedule_message = format_schedule(
            data,
            day=target_date.day,
            month=target_date.month,
            group=group_name
        )

        kb = get_other_group_schedule_keyboard(
            start_date=keyboard_start or target_date,
            selected_date=target_date
        )

        if callback:
            await callback.message.edit_text(
                text=schedule_message,
                reply_markup=kb,
                parse_mode="HTML"
            )
            await callback.answer()
        elif message:
            await message.answer(
                text=schedule_message,
                reply_markup=kb,
                parse_mode="HTML"
            )

        write_user_log(
            f"Пользователь {user_fullname} ({user_id}) просмотрел расписание группы {group_name} на {target_date.strftime('%d.%m')}"
        )

    except FileNotFoundError:
        await (callback.message if callback else message).answer(
            text=f"❌ Не найдено расписание для группы {group_name}.",
            reply_markup=get_back_inline_keyboard("schedule")
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(f"TelegramBadRequest: {e}")