# utils/set_user_birthdate.py
from datetime import datetime
import pytz
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from states.birthdate import BirthdayStates
from utils.logger import write_user_log
from services.birthdate_service import save_user_birthday

router = Router()

# Обработчик для нажатия инлайн-кнопки «Указать дату дня рождения»
@router.callback_query(F.data == "start_birthdate_input")
async def start_birthdate_input(callback: types.CallbackQuery, state: FSMContext):
    # Формируем reply-клавиатуру для выбора дня
    buttons = [KeyboardButton(text=str(day)) for day in range(1, 32)]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[buttons[i:i+7] for i in range(0, len(buttons), 7)],
        resize_keyboard=True
    )

    # редактируем старое сообщение, убрав inline-кнопку
    await callback.message.delete()

    # отправляем новое сообщение с reply-клавиатурой
    await callback.message.answer("Выберите день рождения:", reply_markup=keyboard)

    await state.set_state(BirthdayStates.day)
    await callback.answer()

# Обработчик для выбора дня (reply-клавиатура)
@router.message(BirthdayStates.day)
async def select_day(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личной переписке с ботом.")
        return

    if message.text.isdigit() and 1 <= int(message.text) <= 31:
        await state.update_data(day=int(message.text))
        # Формируем reply-клавиатуру для выбора месяца
        buttons = [KeyboardButton(text=str(i)) for i in range(1, 13)]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[buttons[i:i+4] for i in range(0, len(buttons), 4)],
            resize_keyboard=True
        )
        await message.answer("Выберите месяц рождения:", reply_markup=keyboard)
        await state.set_state(BirthdayStates.month)
    else:
        await message.answer("Пожалуйста, выберите корректный день.")

# Обработчик для выбора месяца (reply-клавиатура)
@router.message(BirthdayStates.month)
async def select_month(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личной переписке с ботом.")
        return

    if message.text.isdigit() and 1 <= int(message.text) <= 12:
        await state.update_data(month=int(message.text))
        tz_moscow = pytz.timezone("Europe/Moscow")
        current_year = datetime.now(tz=tz_moscow).year
        # Формируем reply-клавиатуру для выбора года (от current_year-100 до current_year)
        buttons = [KeyboardButton(text=str(year)) for year in range(current_year - 100, current_year + 1)]
        # Разбиваем кнопки на ряды по 5
        keyboard = ReplyKeyboardMarkup(
            keyboard=[buttons[i:i+5] for i in range(0, len(buttons), 5)],
            resize_keyboard=True
        )
        await message.answer("Выберите год рождения:", reply_markup=keyboard)
        await state.set_state(BirthdayStates.year)
    else:
        await message.answer("Пожалуйста, выберите корректный месяц.")

# Обработчик для выбора года и сохранения данных (reply-клавиатура)
@router.message(BirthdayStates.year)
async def save_birthday(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личной переписке с ботом.")
        return

    tz_moscow = pytz.timezone("Europe/Moscow")
    current_year = datetime.now(tz=tz_moscow).year

    if message.text.isdigit() and 1900 <= int(message.text) <= current_year:
        await state.update_data(year=int(message.text))
        data = await state.get_data()
        day = data.get("day")
        month = data.get("month")
        year = data.get("year")
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

        # Сохраняем дату рождения в базу
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
        message_to_user = f"Дата вашего рождения {formatted_date} сохранена."
        await save_user_birthday(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
            day=day,
            month=month,
            year=year,
            message=message
        )
        write_user_log(f"Пользователь {user_name} ({user_id}) установил дату рождения на {day}.{month}.{year}")
        await state.clear()
    else:
        await message.answer("Пожалуйста, выберите корректный год.")
