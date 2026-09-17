from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from keyboards.profile_menu_keyboard import get_profile_menu_inline_keyboard
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from services.profile.info import get_profile_info_service


info_router = Router()


@info_router.message(Command("profile"))
@private_only
@sync_username
async def profile_info_command(msg: Message):
    user = msg.from_user
    user_id = user.id
    result = get_profile_info_service(user_id)

    await msg.answer(
        text=result.msg_to_user,
        reply_markup=get_profile_menu_inline_keyboard()
    )
