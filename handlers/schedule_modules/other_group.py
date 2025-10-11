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

router = Router()

tz_moscow = pytz.timezone("Europe/Moscow")


@router.callback_query(F.data == "other_group")
async def choose_other_group_schedule(callback: CallbackQuery, state: FSMContext):
    """Запросить у пользователя ввод номер другой группы"""
    write_user_log(f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку ввода другой группы")
    await callback.answer()
    await callback.message.edit_text(
        text="Введите номер группы, расписание которой хотите посмотреть (например, ИДБ-23-10):",
        reply_markup=get_cancel_inline_keyboard()
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


@router.callback_query(F.data.startswith("schedule_other_date_"))
async def handle_other_schedule_date(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопок переключения дней"""
    date_str = callback.data.split("_")[-1]
    data = await state.get_data()
    group_name = data.get("group_name")
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz_moscow)

    await show_other_schedule_for_date(
        user_id=callback.from_user.id,
        user_fullname=callback.from_user.full_name,
        group_name=group_name,
        target_date=target_date,
        callback=callback
    )


async def show_other_schedule_for_date(
        user_id: int, user_fullname: str, group_name: str, target_date: datetime,
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

        kb = get_other_group_schedule_keyboard(target_date)

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