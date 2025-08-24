from aiogram import types, Router
from aiogram.filters import Command

from utils.logger import write_user_log
from utils.user_utils import get_user_name
from keyboards.birthdate import get_birthdate_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()

# Обработчик команды /birthdate
@router.message(Command("birthdate"))
@private_only
@ensure_user_in_db
@sync_username
async def birthdate_msg(message: types.Message):

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /birthdate"
    write_user_log(msg)

    UserNAME = await get_user_name(message)

    keyboard = get_birthdate_inline_keyboard()

    await message.answer(
        f"Привет, {UserNAME}! Нажми на кнопку, чтобы указать дату своего рождения.", reply_markup=keyboard
    )