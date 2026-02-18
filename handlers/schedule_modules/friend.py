from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from datetime import datetime, timedelta

import pytz

from handlers.schedule import show_schedule_for_date

tz_moscow = pytz.timezone("Europe/Moscow")

router = Router()


@router.callback_query(F.data.startswith("friend_schedule_"))
async def show_friend_schedule(callback: CallbackQuery):
    # Разбираем fid из callback_data
    fid = int(callback.data.split("_")[-1])

    today = datetime.now(tz=tz_moscow)

    await show_schedule_for_date(
        user_id=callback.from_user.id,
        user_fullname=callback.from_user.full_name,
        target_date=today,
        callback=callback,
        friend_id=fid
    )

    await callback.answer()