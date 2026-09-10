from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.contest import get_contest_info_keyboard

from services.contest import check_conditions

from utils.user_utils import get_user_name
from utils.logger import write_user_log


info_router = Router()


@info_router.callback_query(F.data == "contest")
async def send_contest_info(callback: CallbackQuery):
    user = callback.from_user
    user_name = await get_user_name(user)

    await callback.message.edit_text(
        text=(
            f"Привет, {user_name}!\n\n{check_conditions(user.id)}"
        ),
        parse_mode="HTML",
        reply_markup=get_contest_info_keyboard(),
    )

    write_user_log(f"Пользователь {user.full_name} ({user.id}) {user.username} открыл страницу розыгрыша")

    await callback.answer()