from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.search_profile import SearchProfileState
from keyboards.cancel_keyboard import get_cancel_inline_keyboard
from keyboards.search_profile import get_search_profile_keyboard
from utils.logger import write_user_log
from services.search_profile import (
    get_search_profile_msg,
    get_user_profile_msg,
    get_invalid_username_text
)

search_router = Router()


@search_router.message(Command("search"))
async def search_profile_command(msg: Message, state: FSMContext):
    user = msg.from_user
    await msg.answer(
        text=get_search_profile_msg(user),
        reply_markup=get_cancel_inline_keyboard("start")
    )
    await state.set_state(SearchProfileState.choosing_username)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} ввёл команду /search")


@search_router.callback_query(F.data == "search_profile")
async def search_profile_callback(clb: CallbackQuery, state: FSMContext):
    user = clb.from_user
    await clb.message.edit_text(
        text=get_search_profile_msg(user),
        reply_markup=get_cancel_inline_keyboard("start")
    )
    await state.set_state(SearchProfileState.choosing_username)
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} открыл меню поиска пользователей")


@search_router.message(StateFilter(SearchProfileState.choosing_username))
async def render_search_profile(msg: Message, state: FSMContext):
    user = msg.from_user
    user_name = msg.text.strip().lstrip("@")
    if not (2 <= len(user_name) <= 50):
        await msg.answer(
            text=get_invalid_username_text(),
            reply_markup=get_cancel_inline_keyboard("start")
        )
        write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} не смог получить профиль, @{user_name} невалидный")
        return

    status, response_text = get_user_profile_msg(user_name, user.id)

    await msg.answer(
        text=response_text,
        reply_markup=get_search_profile_keyboard()
    )
    await state.clear()

    if status:
        write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} смог получить профиль @{user_name}")
    else:
        write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} не смог получить профиль @{user_name}")



