# handlers/help

from aiogram import Router, types
from aiogram.filters import Command

from utils.logger import write_user_log
from utils.user_utils import get_user_name

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()

@router.message(Command("help"))
@private_only
@ensure_user_in_db
@sync_username
async def help_msg(message: types.Message):

    UserNAME = await get_user_name(message)

    await message.answer(
        f"Привет, {UserNAME}!\n\n"
        "Я — бот Stankin-MultiTool! 🤖\n"
        "Моя задача — помогать студентам Станкина: поздравлять их с днём рождения 🎉 и отправлять актуальное расписание занятий 📅."
    )
    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) запросил информацию о боте"
    write_user_log(msg)