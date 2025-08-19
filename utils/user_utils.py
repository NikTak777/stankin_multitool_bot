from aiogram import types
from utils.database import get_real_user_name
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from bot import bot

async def get_user_name(message: types.Message) -> str:
    """Возвращает настоящее имя пользователя, если оно есть в БД, иначе — Telegram full_name."""
    user_id = message.from_user.id
    user_name = get_real_user_name(user_id)

    return user_name if user_name else message.from_user.full_name

async def is_admin(chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь админом или владельцем группы."""
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner))