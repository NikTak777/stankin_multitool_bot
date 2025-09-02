# decorators/group_only.py
from functools import wraps
from aiogram.types import Message

from config import ADMIN_ID


def admin_only(handler):
    """Декоратор: разрешает выполнение хэндлера только для админа бота"""
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        print(message, " ", args, " ", kwargs)
        if message.from_user.id != ADMIN_ID:
            await message.answer("❌ У вас нет прав для выполнения этой команды.")
            return
        return await handler(message, *args, **kwargs)
    return wrapper
