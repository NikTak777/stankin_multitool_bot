from aiogram import types, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from utils.logger import write_user_log
from utils.database import update_user_wishlist

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db
from decorators.require_birthdate import require_birthdate

router = Router()

# Обработчик команды /my_wishlist
@router.message(Command("my_wishlist"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_user_wishlist(message: types.Message, state: FSMContext):

    msg = f"Пользователь {message.from_user.full_name} ({message.from_user.id}) ввёл команду /my_wishlist"
    await write_user_log(msg)

    await process_user_wishlist(message.from_user, message, state, is_callback=False)

# Обработчик callback-кнопки
@router.callback_query(lambda c: c.data == "my_wishlist")
async def callback_user_wishlist(callback: CallbackQuery, state: FSMContext):

    msg = f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) нажал кнопку для просмотра своего вишлиста"
    write_user_log(msg)

    await callback.answer()
    await process_user_wishlist(callback.from_user, callback.message, state, is_callback=True)

# Универсальная функция для запроса нового вишлиста пользователя
@require_birthdate("user_wishlist")
async def process_user_wishlist(user, message_obj, state: FSMContext, is_callback=False):

    msg_to_user = f"Пожалуйста, введите вишлист одним сообщением через запятую:"

    if is_callback:
        await message_obj.edit_text(msg_to_user)
    else:
        await message_obj.answer(msg_to_user, reply_markup=ReplyKeyboardRemove())

    await state.set_state("awaiting_user_wishlist")

# Хэндлер, когда пользователь ввёл свой вишлист
@router.message(StateFilter("awaiting_user_wishlist"))
async def show_user_wishlist(message: types.Message, state: FSMContext):

    new_wishlist = message.text.strip()

    if len(new_wishlist) < 2 or len(new_wishlist) > 100:  # Пример проверки длины вишлиста
        await message.answer("Вишлист должен быть от 2 до 100 символов. Попробуйте еще раз.")
        return

    UserID = message.from_user.id

    update_user_wishlist(UserID, new_wishlist)
    await message.answer(f"Ваш новый вишлист успешно сохранен: {new_wishlist}")
    msg = f"Пользователь {message.from_user.full_name} ({UserID}) установил новый вишлист: {new_wishlist}"
    await write_user_log(msg)
    await state.clear()