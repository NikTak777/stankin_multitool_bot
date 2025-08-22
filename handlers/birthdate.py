from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from utils.logger import write_user_log
from utils.database import get_user_info, check_user_exists
from utils.user_utils import get_user_name
from keyboards.birthdate import get_birthdate_inline_keyboard

router = Router()

# Обработчик команды /birthdate
@router.message(Command("birthdate"))
async def birthdate_msg(message: types.Message):
    if message.chat.type != "private":
        await message.answer("Эта команда доступна только в личной переписке с ботом.")
        return

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /birthdate"
    write_user_log(msg)

    UserNAME = await get_user_name(message)

    keyboard = get_birthdate_inline_keyboard()

    await message.answer(
        f"Привет, {UserNAME}! Нажми на кнопку, чтобы указать дату своего рождения.", reply_markup=keyboard
    )