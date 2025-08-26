from aiogram import Router, F, types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta

import pytz

from services.schedule_service import get_schedule_for_date
from keyboards.schedule_keyboards import get_custom_schedule_keyboard, get_week_days_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard
from states.schedule import ScheduleState
from utils.logger import write_user_log
from utils.user_utils import check_group_user

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()

tz_moscow = pytz.timezone("Europe/Moscow")


# --- Обработчик для команды /schedule ---
@router.message(Command("schedule"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_schedule(message: types.Message, state: FSMContext, bot: Bot):

    write_user_log(f"Пользователь {message.from_user.full_name} ({message.from_user.id}) запросил расписание")

    user_has_group = await check_group_user(message.from_user, state, bot, message=message, from_schedule=True)
    if not user_has_group:
        return

    today = datetime.now(tz=tz_moscow)
    await show_schedule_for_date(message.from_user.id, message.from_user.full_name, today, message=message)


# --- Обработчик для инлайн-кнопки ---
@router.callback_query(F.data == "schedule")
async def show_today_schedule(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user_has_group = await check_group_user(callback.from_user, state, bot, callback=callback)
    if not user_has_group:
        return

    today = datetime.now(tz=tz_moscow)
    await show_schedule_for_date(callback.from_user.id, callback.from_user.full_name, today, callback=callback)
    await callback.answer()


# --- Кнопка выбора дня ---
@router.callback_query(F.data.startswith("schedule_offset_"))
async def handle_day_offset(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    offset = int(callback.data.split("_")[-1])
    today = datetime.now(tz=tz_moscow)
    target_date = today + timedelta(days=offset)
    while target_date.weekday() == 6:  # пропускаем воскресенье
        target_date += timedelta(days=1)

    user_has_group = await check_group_user(callback.from_user, state, bot, callback=callback)
    if not user_has_group:
        return

    await show_schedule_for_date(
        user_id=callback.from_user.id,
        user_fullname=callback.from_user.full_name,
        target_date=target_date,
        callback=callback
    )


# --- Выбор произвольного дня ---
@router.callback_query(F.data == "schedule_custom")
async def choose_custom_day(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    # Генерируем клавиатуру с днями месяца
    buttons = [[types.KeyboardButton(text=str(i)) for i in range(j, min(j + 7, 32))] for j in range(1, 32, 7)]
    builder = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await callback.message.answer(
        "Выберите день:",
        reply_markup=builder
    )
    await state.set_state(ScheduleState.choosing_day)
    await callback.answer()


# --- Обработка выбора дня ---
@router.message(ScheduleState.choosing_day)
async def choose_custom_month(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 31:
        await state.update_data(day=int(message.text))

        # Клавиатура с месяцами
        month_buttons = [[types.KeyboardButton(text=str(i)) for i in range(j, min(j + 4, 13))] for j in range(1, 13, 4)]
        builder = types.ReplyKeyboardMarkup(keyboard=month_buttons, resize_keyboard=True)

        await message.answer(
            "Выберите месяц:",
            reply_markup=builder
        )
        await state.set_state(ScheduleState.choosing_month)
    else:
        await message.answer("Пожалуйста, выберите корректный день (1–31):")


# --- Обработка выбора месяца и показ расписания ---
@router.message(ScheduleState.choosing_month)
async def show_custom_schedule(message: types.Message, state: FSMContext, bot: Bot):
    if message.text.isdigit() and 1 <= int(message.text) <= 12:
        await state.update_data(month=int(message.text))
        data = await state.get_data()
        day, month = data["day"], data["month"]

        user_id = message.from_user.id
        user_fullname = message.from_user.full_name

        # Проверяем группу пользователя
        user_has_group = await check_group_user(message.from_user, state, bot, message=message)
        if not user_has_group:
            return

        tmp_msg = await message.answer("...", reply_markup=types.ReplyKeyboardRemove())
        await tmp_msg.delete()

        # Получаем расписание
        schedule_message = get_schedule_for_date(user_id, day, month)

        if schedule_message is None or schedule_message == "incorrect date":
            # Ошибка даты
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Выбрать другой день", callback_data="schedule_custom")]
            ])
            await message.answer(
                "❌ Неверная дата. Проверьте правильность введённых дня и месяца.\nХотите выбрать другой день?",
                reply_markup=keyboard
            )
            write_user_log(f"Пользователь {user_fullname} ({user_id}) ввёл некорректную дату {day}.{month}")
        else:

            target_date = datetime(message.date.year, month, day, tzinfo=tz_moscow)

            await show_custom_schedule_for_date(
                user_id=user_id,
                user_fullname=user_fullname,
                target_date=target_date,
                message=message
            )
            write_user_log(f"Пользователь {user_fullname} ({user_id}) посмотрел расписание на {day}.{month}")

        await state.clear()
    else:
        await message.answer("Пожалуйста, выберите корректный месяц (1–12):")


@router.callback_query(F.data.startswith("schedule_date_"))
async def handle_custom_schedule_date(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    date_str = callback.data.split("_")[-1]
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz_moscow)

    user_has_group = await check_group_user(callback.from_user, state, bot, callback=callback)
    if not user_has_group:
        return

    await show_custom_schedule_for_date(
        user_id=callback.from_user.id,
        user_fullname=callback.from_user.full_name,
        target_date=target_date,
        callback=callback
    )

# --- Общая функция для показа расписания ---
async def show_schedule_for_date(
    user_id: int,
    user_fullname: str,
    target_date: datetime,
    message: types.Message | None = None,
    callback: types.CallbackQuery | None = None,
):
    """Редактирует старое сообщение или отправляет новое с расписанием и клавиатурой."""
    schedule_message = get_schedule_for_date(user_id, target_date.day, target_date.month)

    if not schedule_message:
        if callback:
            await callback.message.edit_text("⚠️ Расписание пока недоступно для вашей группы.", reply_markup=get_back_inline_keyboard("start"))
            await callback.answer()
        elif message:
            await message.answer("⚠️ Расписание пока недоступно для вашей группы.", reply_markup=get_back_inline_keyboard("start"))
        return

    inline_kb = get_week_days_keyboard()

    try:
        if callback:
            # Редактируем старое сообщение с inline-клавиатурой
            await callback.message.edit_text(
                text=schedule_message,
                reply_markup=inline_kb,
                parse_mode="HTML"
            )
            await callback.answer()
        elif message:
            # Новый вызов (/schedule)
            await message.answer(
                text=schedule_message,
                reply_markup=inline_kb,
                parse_mode="HTML"
            )
    except TelegramBadRequest as e:
        # Игнорируем "message is not modified"
        if "message is not modified" not in str(e):
            print(f"TelegramBadRequest: {e}")

    write_user_log(
        f"Пользователь {user_fullname} ({user_id}) посмотрел недельное расписание на {target_date.strftime('%d.%m')}"
    )


# --- Отдельная функция для показа расписания по конкретной дате (с кастомными стрелками) ---
async def show_custom_schedule_for_date(
    user_id: int,
    user_fullname: str,
    target_date: datetime,
    message: types.Message | None = None,
    callback: types.CallbackQuery | None = None,
):
    """Отправляет/редактирует расписание с клавиатурой Вперёд/Назад + выбор новой даты + возврат в меню."""

    schedule_message = get_schedule_for_date(user_id, target_date.day, target_date.month)

    if not schedule_message or schedule_message == "incorrect date":
        text = "⚠️ Расписание пока недоступно для вашей группы."
        if callback:
            await callback.message.edit_text(text, reply_markup=get_back_inline_keyboard("start"))
            await callback.answer()
        elif message:
            await message.answer(text, reply_markup=get_back_inline_keyboard("start"))
        return

    # Клавиатура
    kb = get_custom_schedule_keyboard(target_date)

    try:
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

    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            print(f"TelegramBadRequest: {e}")

    write_user_log(
        f"Пользователь {user_fullname} ({user_id}) посмотрел кастомное расписание на {target_date.strftime('%d.%m')}"
    )