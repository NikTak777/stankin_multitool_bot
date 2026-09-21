from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from states.group_registration import GroupRegistration
from utils.logger import write_user_log
from utils.group_utils import load_groups, save_groups, get_group_name_by_id, is_valid_group_name
from utils.database import add_user_to_db, check_user_exists
from utils.group_utils import is_bot_admin, is_group_registered, is_group_file_exists
from utils.user_utils import is_admin

# Декораторы
from decorators.group_only import group_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


@router.message(Command("init"))
@group_only
@ensure_user_in_db
@sync_username
async def initialization_bot_in_group(message: types.Message, state: FSMContext):

    group_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    if not await is_bot_admin(group_id):
        await message.answer("❌ Бот должен быть администратором группы для работы с регистрацией!")
        return

    groups_list = await load_groups()

    if not await is_admin(group_id, user_id):
        await message.answer("❌ Эта команда доступна только для администраторов группы!")
        return

    write_user_log(f"Админ {user_name} ({user_id}) группы {group_id} начал регистрацию")

    if is_group_registered(group_id, groups_list):
        group_name = get_group_name_by_id(group_id, groups_list)
        await message.answer(f"✅ Эта группа уже зарегистрирована! Ваш номер — {group_name}")
        write_user_log(
            f"Админ {user_name} ({user_id}) закончил регистрацию. Группа {group_name} {group_id} уже зарегистрирована"
        )
        if not is_group_file_exists(group_name):
            await message.answer("⚠️ Пока расписание вашей группы отсутствует в системе.")
        return

    await state.update_data(init_user_id=user_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🚫 Отменить регистрацию", callback_data="cancel_registration")]]
    )

    await message.answer(
        f"Привет, {user_name}!\n❌ Ваша группа ещё не зарегистрирована. Укажите её номер (например, ИДБ-23-10):",
        reply_markup=keyboard
    )
    await state.set_state(GroupRegistration.waiting_for_group_name)


@router.callback_query(lambda c: c.data == "cancel_registration")
async def cancel_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    group_id = callback.message.chat.id

    if not await is_admin(group_id, user_id):
        await callback.answer("❌ Только администратор может отменить регистрацию!", show_alert=True)
        return

    write_user_log(f"Кнопка 'Отменить регистрацию' нажата пользователем {user_name} ({user_id}) в группе {group_id}")
    await callback.message.edit_text("✅ Регистрация отменена.")
    await callback.answer()


@router.message(GroupRegistration.waiting_for_group_name)
async def process_group_name(message: types.Message, state: FSMContext):
    group_id = message.chat.id
    user_id = message.from_user.id
    user_data = await state.get_data()

    if user_id != user_data.get("init_user_id"):
        return

    group_name = message.text.strip()
    groups = await load_groups()

    if not is_valid_group_name(group_name):
        await message.answer("⚠️ Номер группы введён некорректно!\nФормат: XXX-00-00 (например, ИДБ-23-10).")
        return

    if group_name in groups:
        await message.answer("❌ Такая группа уже зарегистрирована! Введите другой номер:")
        return

    groups[group_name] = {"chat_id": group_id, "registered_by": user_id, "send_hour": 20}
    await save_groups(groups)

    await message.answer(f"✅ Группа {group_name} успешно зарегистрирована!")
    write_user_log(f"Админ {message.from_user.full_name} ({user_id}) зарегистрировал группу {group_name} ({group_id})")
    await state.clear()

    if not is_group_file_exists(group_name):
        await message.answer("⚠️ Пока расписание вашей группы отсутствует в системе.")
