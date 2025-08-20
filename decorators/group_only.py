# decorators/group_only.py
from functools import wraps
from aiogram.types import Message

def group_only(handler):
    """Декоратор: разрешает выполнение хэндлера только в группах или супергруппах."""
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        if message.chat.type not in ["group", "supergroup"]:
            await message.answer("❌ Эта команда доступна только в группах.")
            return
        return await handler(message, *args, **kwargs)
    return wrapper
