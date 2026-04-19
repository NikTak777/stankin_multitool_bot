# decorators/private_only.py
from functools import wraps
from typing import Union
from aiogram.types import CallbackQuery, Message


def private_only(handler):
    """Декоратор: разрешает выполнение хэндлера только в приватных чатах."""
    @wraps(handler)
    async def wrapper(event: Union[Message, CallbackQuery], *args, **kwargs):
        chat = None
        if isinstance(event, CallbackQuery):
            if event.message:
                chat = event.message.chat
        else:
            chat = event.chat

        if chat is None or chat.type != "private":
            text = "❌ Эта команда доступна только в личной переписке с ботом."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            else:
                await event.answer(text)
            return
        return await handler(event, *args, **kwargs)
    return wrapper
