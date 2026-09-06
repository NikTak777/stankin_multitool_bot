from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.back_to_menu import get_back_inline_keyboard

from services.contest import check_conditions

from utils.database_utils.friends import get_friends_info
from utils.time import get_now_time


info_router = Router()


@info_router.callback_query(F.data == "contest")
async def send_contest_info(callback: CallbackQuery):
    user = callback.from_user

    now = get_now_time()

    await callback.message.edit_text(
        text=(
            f"Привет, {user.full_name}\n\n{check_conditions(user.id)}"
        ),
        reply_markup=get_back_inline_keyboard("start"),
        parse_mode="HTML"
    )
    await callback.answer()