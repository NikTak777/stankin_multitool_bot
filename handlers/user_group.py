from aiogram import types, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from utils.logger import write_user_log
from utils.group_utils import is_valid_group_name, is_group_file_exists, format_subgroup
from utils.database import set_user_group_subgroup
from states.group_state import GroupSelectState

from keyboards.back_to_menu import get_back_inline_keyboard
from keyboards.cancel_keyboard import get_cancel_inline_keyboard
from keyboards.group import (
    get_enter_code_group_keyboard,
    get_select_year_group_keyboard,
    get_select_name_group_keyboard,
    get_select_subgroup_keyboard
)

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


# Обработчик команды /group
@router.message(Command("group"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_user_group(message: Message, state: FSMContext):
    write_user_log(f"Пользователь {message.from_user.full_name} ({message.from_user.id}) вызвал /group")
    await message.answer(
        text=(
            "Выберете код вашей группы\n"
            "   или\n"
            "Введите номер вашей группы (например, ИДБ-23-10):"
        ),
        reply_markup = await get_enter_code_group_keyboard()
    )
    await state.set_state(GroupSelectState.choosing_code)


# Выбор кода группы ХХХ через inline-клавиатуру
@router.callback_query(F.data == "group")
@sync_username
async def user_code_group_input(callback: CallbackQuery, state: FSMContext):
    write_user_log(f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку ввода группы")
    await callback.answer()
    await callback.message.edit_text(
        text=(
            "Выберете код вашей группы\n"
            "   или\n"
            "Введите номер вашей группы (например, ИДБ-23-10):"
        ),
        reply_markup = await get_enter_code_group_keyboard()
    )
    await state.set_state(GroupSelectState.choosing_code)


# Выбор года группы 00 через inline-клавиатуру
@router.callback_query(StateFilter(GroupSelectState.choosing_code), F.data.startswith("group_code_"))
async def user_year_group_input(callback: CallbackQuery, state: FSMContext):
    selected_code = callback.data.split("_")[2]
    await state.update_data(group_code=selected_code)

    # await message.answer("Введите номер вашей подгруппы (например, А или Б):", reply_markup=ReplyKeyboardRemove())
    await callback.message.edit_text(
        text="Выберете год поступления вашей группы",
        reply_markup = await get_select_year_group_keyboard(selected_code)
    )
    await state.set_state(GroupSelectState.choosing_year)


# Выбор названия группы XXX-00-00(prefix) через inline-клавиатуру
@router.callback_query(StateFilter(GroupSelectState.choosing_year), F.data.startswith("group_year_"))
async def user_name_group_input(callback: CallbackQuery, state: FSMContext):
    selected_year = callback.data.split("_")[2]
    await state.update_data(group_year=selected_year)
    selected_code = (await state.get_data())["group_code"]

    await callback.message.edit_text(
        "Выберете вашу группу:",
        reply_markup = await get_select_name_group_keyboard(selected_code, selected_year)
    )
    await state.set_state(GroupSelectState.choosing_group)


# Выбор подгруппы А или Б через inline-клавиатуру
@router.callback_query(StateFilter(GroupSelectState.choosing_group), F.data.startswith("group_name_"))
async def user_name_subgroup_input(callback: CallbackQuery, state: FSMContext):
    selected_group = callback.data.split("_")[2]
    await state.update_data(group_name=selected_group)

    await callback.message.edit_text(
        "Выберете вашу подгруппу:",
        reply_markup = await get_select_subgroup_keyboard()
    )
    await state.set_state(GroupSelectState.choosing_subgroup)


# Сохранение данных о группе и подгруппе
@router.callback_query(StateFilter(GroupSelectState.choosing_subgroup), F.data.startswith("subgroup_"))
async def process_subgroup_input(callback: CallbackQuery, state: FSMContext):
    selected_subgroup = callback.data.split("_")[1].upper()
    user_data = await state.get_data()
    user_group = user_data.get("group_name")
    from_schedule = user_data.get("from_schedule", False)
    back_to = "start" if from_schedule else "info"

    set_user_group_subgroup(callback.from_user.id, user_group, selected_subgroup)

    msg = f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) указал группу: {user_group}, подгруппа: {selected_subgroup}"
    write_user_log(msg)

    msg_to_user = f"✅ Данные сохранены: Группа {user_group}, Подгруппа {format_subgroup(selected_subgroup)}."

    if not await is_group_file_exists(user_group):
        msg_to_user += f"\n\n⚠️ К сожалению, пока вы не можете смотреть расписание вашей группы, так как оно не появилось в системе."

    await callback.message.edit_text(
        text=msg_to_user,
        reply_markup=get_back_inline_keyboard(back_to)
    )
    await state.clear()


@router.message(StateFilter(GroupSelectState.choosing_code))
async def user_full_group_input(message: Message, state: FSMContext):
    selected_group = message.text

    if not is_valid_group_name(selected_group):
        await message.answer(
            text=(
                "⚠️ Номер группы некорректный!\n\n"
                "Выберете код вашей группы\n"
                "   или\n"
                "Введите в формате XXX-00-00 (например, ИДБ-23-10):"
            ),
            reply_markup = await get_enter_code_group_keyboard()
        )
        return

    await state.update_data(group_name=selected_group)
    await message.answer(
        text="Выберете вашу подгруппу:",
        reply_markup=await get_select_subgroup_keyboard()
    )
    await state.set_state(GroupSelectState.choosing_subgroup)


