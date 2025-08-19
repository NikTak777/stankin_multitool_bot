from aiogram import types, Router
from aiogram.filters import Command
from utils.database import check_user_exists, add_user_to_db
from utils.logger import write_user_log
from utils.user_utils import get_user_name
from keyboards.start import get_start_inline_keyboard
from decorators.private_only import private_only

router = Router()

@router.message(Command("start"))
@private_only
async def start_msg(message: types.Message):

    user_id = message.from_user.id
    user_name = await get_user_name(message)

    write_user_log(f"Пользователь {message.from_user.full_name} ({user_id}) ввёл команду /start")

    if not check_user_exists(user_id):
        add_user_to_db(user_id, message.from_user.username, message.from_user.full_name)
        msg = f"Пользователь {message.from_user.full_name} ({user_id}) добавлен в базу данных"
        await write_user_log(msg)

    inline_keyboard = get_start_inline_keyboard()

    await message.answer(
        f"Привет, {user_name}! Нажми на кнопку, чтобы выбрать действие:",
        reply_markup=inline_keyboard
    )
