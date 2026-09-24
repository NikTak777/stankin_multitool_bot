from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.logger import write_user_log
from states.group_state import GroupSelectState
from keyboards.back_to_menu import get_back_inline_keyboard
from services.profile.edit.group import (
    get_code_input_text,
    get_year_input_text,
    get_group_input_text,
    get_subgroup_input_text,
    get_save_group_text,
    get_full_group_input_text
)

from keyboards.group import (
    get_enter_code_group_keyboard,
    get_select_year_group_keyboard,
    get_select_name_group_keyboard,
    get_select_subgroup_keyboard
)

group_router = Router()


@group_router.message(Command("group"))
async def cmd_profile_group(msg: Message, state: FSMContext):
    user = msg.from_user
    await msg.answer(
        text=get_code_input_text(),
        reply_markup = await get_enter_code_group_keyboard()
    )
    await state.set_state(GroupSelectState.choosing_code)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} вызвал команду /group")


@group_router.callback_query(F.data == "group")
async def profile_code_group_input(clb: CallbackQuery, state: FSMContext):
    user = clb.from_user
    await clb.message.edit_text(
        text=get_code_input_text(),
        reply_markup = await get_enter_code_group_keyboard(callback_target="info")
    )
    await clb.answer()
    await state.set_state(GroupSelectState.choosing_code)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} нажал кнопку ввода группы")


@group_router.callback_query(GroupSelectState.choosing_code, F.data.startswith("group_code_"))
async def profile_year_group_input(clb: CallbackQuery, state: FSMContext):
    user = clb.from_user
    selected_code = clb.data.split("_")[2]
    await state.update_data(group_code=selected_code)
    await clb.message.edit_text(
        text=get_year_input_text(),
        reply_markup = await get_select_year_group_keyboard(selected_code, callback_target="info")
    )
    await clb.answer()
    await state.set_state(GroupSelectState.choosing_year)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} ввёл код группы {selected_code}")


@group_router.callback_query(GroupSelectState.choosing_year, F.data.startswith("group_year_"))
async def profile_name_group_input(clb: CallbackQuery, state: FSMContext):
    user = clb.from_user
    selected_year = clb.data.split("_")[2]
    await state.update_data(group_year=selected_year)
    selected_code = (await state.get_data())["group_code"]
    await clb.message.edit_text(
        text=get_group_input_text(),
        reply_markup = await get_select_name_group_keyboard(selected_code, selected_year, callback_target="info")
    )
    await clb.answer()
    await state.set_state(GroupSelectState.choosing_group)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} ввёл год группы {selected_year}")


@group_router.callback_query(GroupSelectState.choosing_group, F.data.startswith("group_name_"))
async def profile_name_subgroup_input(clb: CallbackQuery, state: FSMContext):
    user = clb.from_user
    selected_group = clb.data.split("_")[2]
    await state.update_data(group_name=selected_group)
    await clb.message.edit_text(
        text=get_subgroup_input_text(),
        reply_markup = await get_select_subgroup_keyboard()
    )
    await clb.answer()
    await state.set_state(GroupSelectState.choosing_subgroup)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} "
                   f"ввёл группу {selected_group} через inline-клавиатуру")


@group_router.callback_query(GroupSelectState.choosing_subgroup, F.data.startswith("subgroup_"))
async def profile_subgroup_input(clb: CallbackQuery, state: FSMContext):
    user = clb.from_user
    selected_subgroup = clb.data.split("_")[1].upper()
    user_data = await state.get_data()
    user_group = user_data.get("group_name")
    from_schedule = user_data.get("from_schedule", False)
    msg_to_user, back_to = get_save_group_text(
        user_id=user.id,
        group=user_group,
        subgroup=selected_subgroup,
        from_schedule=from_schedule
    )
    await clb.message.edit_text(
        text=msg_to_user,
        reply_markup=get_back_inline_keyboard(back_to)
    )
    await clb.answer()
    await state.clear()
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} "
                   f"сохранил группу {user_group} и подгруппу {selected_subgroup}")


@group_router.message(GroupSelectState.choosing_code)
async def profile_full_group_input(msg: Message, state: FSMContext):
    user = msg.from_user
    selected_group = msg.text.strip()
    msg_to_user, is_valid = get_full_group_input_text(group=selected_group)
    if not is_valid:
        await msg.answer(
            text=msg_to_user,
            reply_markup = await get_enter_code_group_keyboard()
        )
        write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} "
                       f"вручную ввёл невалидный номер группы {selected_group}")
        return
    else:
        await msg.answer(
            text=msg_to_user,
            reply_markup = await get_select_subgroup_keyboard()
        )
        await state.update_data(group_name=selected_group)
        await state.set_state(GroupSelectState.choosing_subgroup)
        write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} "
                       f"вручную ввёл валидный номер группы {selected_group}")
