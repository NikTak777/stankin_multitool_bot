# utils/set_user_birthdate.py
from datetime import datetime
import pytz
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from states.birthdate import BirthdayStates
from utils.logger import write_user_log
from services.birthdate_service import save_user_birthday
from filters.require_fsm import RequireFSM

from keyboards.cancel_keyboard import get_cancel_inline_keyboard

from decorators.private_only import private_only
from decorators.sync_username import sync_username

router = Router()


def _get_day_keyboard():
    """Клавиатура выбора дня для перезапуска потока."""
    buttons = [KeyboardButton(text=str(day)) for day in range(1, 32)]
    return ReplyKeyboardMarkup(
        keyboard=[buttons[i:i+7] for i in range(0, len(buttons), 7)],
        resize_keyboard=True
    )


async def _restart_birthdate_flow(message: types.Message, state: FSMContext):
    """Перезапуск ввода даты рождения (при отсутствии нужных данных в state)."""
    await state.clear()
    sent = await message.answer(
        "Сессия сброшена. Выберите день рождения:",
        reply_markup=_get_day_keyboard()
    )
    await state.update_data(keyboard_message_id=sent.message_id, keyboard_chat_id=sent.chat.id)
    await state.set_state(BirthdayStates.day)


# Обработчик для нажатия инлайн-кнопки «Указать дату дня рождения»
@router.callback_query(F.data == "start_birthdate_input")
@private_only
@sync_username
async def start_birthdate_input(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите дату вашего рождения. Если вы передумали вносить данные, нажмите кнопку 'Отменить'",
        reply_markup=get_cancel_inline_keyboard("edit_profile_menu")
    )

    sent = await callback.message.answer(
        "Шаг 1 из 3:\nВыберите день рождения:",
        reply_markup=_get_day_keyboard()
    )
    await state.update_data(keyboard_message_id=sent.message_id, keyboard_chat_id=sent.chat.id)

    await state.set_state(BirthdayStates.day)
    await callback.answer()

# Обработчик для выбора дня (reply-клавиатура)
@router.message(BirthdayStates.day)
async def select_day(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 31:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        await state.update_data(day=int(message.text))

        data = await state.get_data()
        kmid, kcid = data.get("keyboard_message_id"), data.get("keyboard_chat_id")
        if kmid is not None and kcid is not None:
            try:
                await message.bot.delete_message(chat_id=kcid, message_id=kmid)
            except TelegramBadRequest:
                pass

        buttons = [KeyboardButton(text=str(i)) for i in range(1, 13)]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[buttons[i:i+4] for i in range(0, len(buttons), 4)],
            resize_keyboard=True
        )
        sent = await message.answer(
            "Шаг 2 из 3:\nВыберите месяц рождения:",
            reply_markup=keyboard
        )
        await state.update_data(keyboard_message_id=sent.message_id, keyboard_chat_id=sent.chat.id)
        await state.set_state(BirthdayStates.month)
    else:
        await message.answer("Пожалуйста, выберите корректный день.")

# Обработчик для выбора месяца (reply-клавиатура)
@router.message(BirthdayStates.month, RequireFSM("day"))
async def select_month(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 1 <= int(message.text) <= 12:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        await state.update_data(month=int(message.text))

        data = await state.get_data()
        kmid, kcid = data.get("keyboard_message_id"), data.get("keyboard_chat_id")
        if kmid is not None and kcid is not None:
            try:
                await message.bot.delete_message(chat_id=kcid, message_id=kmid)
            except TelegramBadRequest:
                pass

        tz_moscow = pytz.timezone("Europe/Moscow")
        current_year = datetime.now(tz=tz_moscow).year
        buttons = [KeyboardButton(text=str(year)) for year in range(current_year - 100, current_year + 1)]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[buttons[i:i+5] for i in range(0, len(buttons), 5)],
            resize_keyboard=True
        )
        sent = await message.answer(
            "Шаг 3 из 3:\nВыберите год рождения:",
            reply_markup=keyboard
        )
        await state.update_data(keyboard_message_id=sent.message_id, keyboard_chat_id=sent.chat.id)
        await state.set_state(BirthdayStates.year)
    else:
        await message.answer("Пожалуйста, выберите корректный месяц.")


@router.message(BirthdayStates.month)
async def select_month_fallback(message: types.Message, state: FSMContext):
    """Обработка сообщения в состоянии месяца при отсутствии дня в state (перезапуск потока)."""
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await _restart_birthdate_flow(message, state)


# Обработчик для выбора года и сохранения данных (reply-клавиатура)
@router.message(BirthdayStates.year, RequireFSM("day", "month"))
async def save_birthday(message: types.Message, state: FSMContext):
    tz_moscow = pytz.timezone("Europe/Moscow")
    current_year = datetime.now(tz=tz_moscow).year

    if message.text.isdigit() and 1900 <= int(message.text) <= current_year:
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        await state.update_data(year=int(message.text))
        data = await state.get_data()
        day = data.get("day")
        month = data.get("month")
        year = data.get("year")
        kmid, kcid = data.get("keyboard_message_id"), data.get("keyboard_chat_id")
        if kmid is not None and kcid is not None:
            try:
                await message.bot.delete_message(chat_id=kcid, message_id=kmid)
            except TelegramBadRequest:
                pass
        error_message = None

        if month == 2:
            if day == 29 and year % 4 != 0:
                error_message = "29 февраля бывает только в високосные годы! Пожалуйста, укажите другой год."
            elif day in (30, 31):
                error_message = "В феврале нет 30 или 31 дня. Укажите корректную дату."
        elif month in [4, 6, 9, 11] and day == 31:
            error_message = "В этом месяце всего 30 дней. Укажите корректную дату."

        if error_message:
            write_user_log(f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл неверную дату рождения")
            # Предлагаем перезапустить ввод даты рождения через инлайн-кнопку
            from keyboards.birthdate import get_birthdate_inline_keyboard
            keyboard = get_birthdate_inline_keyboard()
            await message.answer(error_message, reply_markup=keyboard)
            return

        user_id = message.from_user.id
        user_tag = message.from_user.username
        user_name = message.from_user.full_name
        from utils.database import set_user_birthdate, get_user_info, update_is_approved
        set_user_birthdate(user_id, day, month, year)
        user_info = get_user_info(user_id)
        if not user_info.get("is_approved"):
            update_is_approved(user_id, True)
        from utils.date_utils import format_date
        formatted_date = format_date(day, month, year)
        await save_user_birthday(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            day=day,
            month=month,
            year=year,
            message=message
        )
        write_user_log(f"Пользователь {user_name} ({user_id}) @{user_tag} установил дату рождения на {formatted_date}")
        await state.clear()
    else:
        await message.answer("Пожалуйста, выберите корректный год.")


@router.message(BirthdayStates.year)
async def save_birthday_fallback(message: types.Message, state: FSMContext):
    """Обработка сообщения в состоянии года при отсутствии дня/месяца в state (перезапуск потока)."""
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await _restart_birthdate_flow(message, state)
