from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest

from keyboards.cancel_keyboard import get_cancel_inline_keyboard

from utils.group_utils import load_groups

from utils.database import get_real_user_name, check_user_exists, add_user_to_db, get_user_info
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from bot import bot

from config import ADMIN_ID

async def get_user_name(obj) -> str:
    """Возвращает настоящее имя пользователя, если оно есть в БД, иначе — Telegram full_name."""
    # Определяем, что передано - Message или User
    if hasattr(obj, 'from_user'):
        user = obj.from_user  # Это Message
    else:
        user = obj  # Это User

    user_id = user.id
    user_name = get_real_user_name(user_id)

    # Формируем полное имя из Telegram данных
    full_name = user.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip()
    if not full_name and user.username:
        full_name = f"@{user.username}"

    return user_name if user_name else full_name or "Пользователь"

async def is_admin(chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь админом или владельцем группы."""
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner))

async def check_group_user(
    user: types.User,
    state: FSMContext,
    bot: Bot,
    message: types.Message | None = None,
    callback: types.CallbackQuery | None = None,
    from_schedule: bool = True,
) -> bool:
    """Проверяет наличие группы и подгруппы, если их нет — запрашивает и сохраняет.
       Если message передан — редактируем его, иначе отправляем новое сообщение."""
    user_id = user.id

    # Проверяем, есть ли пользователь
    existing_user = check_user_exists(user_id)
    if not existing_user:
        add_user_to_db(user_id, user.username, user.full_name)

    # Берём инфо
    user_info = get_user_info(user_id)
    user_group, user_subgroup = user_info["user_group"], user_info["user_subgroup"]
    user_name = get_real_user_name(user_id)

    # Если не указаны группа или подгруппа
    if not user_group or not user_subgroup:
        text = f"Привет, {user_name}! Введите номер вашей группы (например, ИДБ-23-10):"

        if callback:
            # Если вызов из инлайн-кнопки — редактируем сообщение
            if callback:
                # редактируем сообщение без ReplyKeyboardRemove
                await callback.message.edit_text(text, reply_markup=get_cancel_inline_keyboard("start"))
                await callback.answer()  # Удаляем эффект загрузки
            elif message:
                # обычное новое сообщение — можно убрать клавиатуру
                await bot.send_message(user_id, text, reply_markup=get_cancel_inline_keyboard("start"))
        elif message:
            # Если вызов из команды /schedule — новое сообщение
            await bot.send_message(user_id, text, reply_markup=get_cancel_inline_keyboard("start"))

        await state.set_state("GroupState:waiting_for_group")
        await state.update_data(from_schedule=from_schedule)
        return False

    return True

async def is_user_accessible(user_id: int) -> bool:
    """Проверяет, доступен ли пользователь для бота."""
    try:
        await bot.get_chat(user_id)
        return True
    except TelegramBadRequest:
        return False


async def is_user_group_admin(user_id: int) -> str | None:
    """
    Проверяет, является ли пользователь старостой (админом) группы.
    Возвращает название группы, если он админ, иначе None.
    """
    groups = await load_groups()

    user_group = next(
        (group for group, data in groups.items() if data.get("registered_by") == user_id),
        None
    )

    return user_group


def is_user_bot_admin(user: types.User) -> bool:
    if user.id == ADMIN_ID:
        return True
    return False