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
                u = event.callback_query.from_user
                log_user_activity(u.id, "callback")

            elif event.message:
                u = event.message.from_user
                if _is_command(event.message):
                    log_user_activity(u.id, "command")
                else:
                    log_user_activity(u.id, "message")

        return await handler(event, data)