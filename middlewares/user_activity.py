# middlewares/user_activity.py
from aiogram import BaseMiddleware, types
from utils.database_utils.database_statistic import log_user_activity


def _is_command(msg: types.Message) -> bool:
    ents = msg.entities or []
    return any(e.type == "bot_command" and e.offset == 0 for e in ents)


class ActivityMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Update):
            if event.callback_query:
                cb = event.callback_query
                if cb.message and cb.message.chat and cb.message.chat.type == "private" and cb.from_user:
                    log_user_activity(cb.from_user.id, "callback")

            elif event.message:
                msg = event.message
                if msg.chat and msg.chat.type == "private" and msg.from_user:
                    ev = "command" if _is_command(msg) else "message"
                    log_user_activity(msg.from_user.id, ev)

        return await handler(event, data)