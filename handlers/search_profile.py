from aiogram import Router, F
from aiogram.filtes import Command
from aiogram.types import Message, CallbackQuery

from services.search_profile import get_search_profile_msg
from keyboards.back_to_menu import get_back_inline_keyboard
from utils.logger import write_user_log

search_router = Router()


@search_router.message(Command("search"))
async def search_profile_command(msg: Message):
    user = msg.from_user
    await msg.answer(
        text=get_search_profile_msg(user),
        reply_markup=get_back_inline_keyboard("start")
    )
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} ввёл команду /search")


@search_router.callback_query(F.data == "search_profile")
async def search_profile_callback(clb: CallbackQuery):
    user = clb.from_user
    await clb.message.edit_text(
        text=get_search_profile_msg(user),
        reply_markup=get_back_inline_keyboard("start")
    )
    write_user_log(f"Пользователь {user.full_name} ({user.id}) @{user.username} открыл меню поиска пользователей")


