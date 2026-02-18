# handlers/friends_menu.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.logger import write_user_log
from utils.user_utils import get_user_name
from utils.database_utils.friends import get_upcoming_birthdays, get_today_birthdays
from keyboards.friends_menu_keyboards import get_friends_menu_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


# Обработчик команды /friends
@router.message(Command("friends"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_friends(message: Message, state: FSMContext):

    await state.clear()

    write_user_log(
        f"Пользователь {message.from_user.full_name} ({message.from_user.id}) @{message.from_user.username} ввёл команду /friends"
    )

    await process_friends_menu(message.from_user, message, is_callback=False)


@router.callback_query(F.data == "friends_menu")
@sync_username
async def callback_friends_menu(callback: CallbackQuery, state: FSMContext):

    await state.clear()

    write_user_log(
        f"Пользователь {callback.from_user.full_name} ({callback.from_user.id}) @{callback.from_user.username} перешёл во вкладку Друзья"
    )

    await process_friends_menu(callback.from_user, callback.message, is_callback=True)
    await callback.answer()


async def process_friends_menu(user, message_obj, is_callback=False):
    user_id = user.id
    user_name = await get_user_name(user)

    upcoming_birthdays = get_upcoming_birthdays(user_id)
    today_birthdays = get_today_birthdays(user_id)

    message_text = f"Привет, {user_name}!"

    if today_birthdays:
        today_birthdays_text = "🎂 Сегодня день рождения у:\n" + "\n".join(
            [f"— {b['user_day']:02d}.{b['user_month']:02d} — {b['user_name']} @{b['user_tag']}\n\t 🎁 Вишлист друга: {b['user_wishlist']}"
             for b in today_birthdays]
        )
    else:
        today_birthdays_text = "🎂 Cегодня дней рождения нет."

    if upcoming_birthdays:
        upcoming_birthdays_text = "🎂 Ближайшие дни рождения:\n" + "\n".join(
            [f"— {b['user_day']:02d}.{b['user_month']:02d} — {b['user_name']} @{b['user_tag']}\n\t 🎁 Вишлист друга: {b['user_wishlist']}"
             for b in upcoming_birthdays]
        )
    else:
        upcoming_birthdays_text = f"🎂 Ближайших дней рождения нет."

    message_text += f"\n\n{today_birthdays_text}\n\n{upcoming_birthdays_text}"

    if is_callback:
        await message_obj.edit_text(message_text, reply_markup=get_friends_menu_keyboard())
        write_user_log(
            f"Пользователь {message_obj.chat.full_name} ({message_obj.chat.id}) @{message_obj.chat.username} получил информацию о друзьях"
        )
    else:
        await message_obj.answer(message_text, reply_markup=get_friends_menu_keyboard())
        write_user_log(
            f"Пользователь {message_obj.from_user.full_name} ({message_obj.from_user.id}) @{message_obj.from_user.username} получил информацию о друзьях"
        )