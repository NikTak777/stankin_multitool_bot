from aiogram import types, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from utils.logger import write_user_log
from utils.group_utils import is_valid_group_name, is_group_file_exists
from utils.database import set_user_group_subgroup
from states.group_state import GroupState
from keyboards.back_to_menu import get_back_inline_keyboard

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
async def cmd_user_group(message: types.Message, state: FSMContext):
    write_user_log(f"Пользователь {message.from_user.full_name} ({message.from_user.id}) вызвал /group")
    await message.answer("Введите номер вашей группы (например, ИДБ-23-10):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(GroupState.waiting_for_group)

# Обработчик callback-кнопки
@router.callback_query(F.data == "group")
async def callback_user_group(callback: CallbackQuery, state: FSMContext):
    write_user_log(f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку ввода группы")
    await callback.answer()
    await callback.message.edit_text("Введите номер вашей группы (например, ИДБ-23-10):")
    await state.set_state(GroupState.waiting_for_group)

# Ввод группы
@router.message(StateFilter(GroupState.waiting_for_group))
async def process_group_input(message: types.Message, state: FSMContext):
    group_name = message.text.strip()

    if not is_valid_group_name(group_name):
        await message.answer("⚠️ Номер группы некорректный! Введите в формате XXX-00-00 (например, ИДБ-23-10):")
        return

    await state.update_data(user_group=group_name)
    await message.answer("Введите номер вашей подгруппы (например, А или Б):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(GroupState.waiting_for_subgroup)

# Ввод подгруппы
@router.message(StateFilter(GroupState.waiting_for_subgroup))
async def process_subgroup_input(message: types.Message, state: FSMContext):
    user_subgroup = message.text.strip().upper()
    user_data = await state.get_data()
    user_group = user_data.get("user_group")

    if user_subgroup not in ["А", "Б"]:
        await message.answer("⚠️ Подгруппа указана неверно! Введите либо 'А', либо 'Б':")
        return

    if user_subgroup == "А":
        user_subgroup = "A"
    elif user_subgroup == "Б":
        user_subgroup = "B"

    set_user_group_subgroup(message.from_user.id, user_group, user_subgroup)

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) указал группу: {user_group}, подгруппа: {user_subgroup}"
    write_user_log(msg)

    msg_to_user = f"✅ Данные сохранены: Группа {user_group}, Подгруппа {user_subgroup}."


    if not await is_group_file_exists(user_group):
        msg_to_user += f"\n\n⚠️ К сожалению, пока вы не можете смотреть расписание вашей группы, так как оно не появилось в системе."

    await message.answer( msg_to_user, reply_markup=get_back_inline_keyboard())
    await state.clear()


