# decorators/private_only.py
from functools import wraps
from aiogram.types import Message

def private_only(handler):
    """Декоратор: разрешает выполнение хэндлера только в приватных чатах."""
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        if message.chat.type != "private":
            await message.answer("❌ Эта команда доступна только в личной переписке с ботом.")
            return
        return await handler(message, *args, **kwargs)
    return wrapper
