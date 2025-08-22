from functools import wraps
from aiogram import types
from utils.database import check_user_exists, add_user_to_db
from utils.logger import write_user_log

def ensure_user_in_db(handler):
    """
    Декоратор: проверяет наличие пользователя в БД.
    Если нет — добавляет.
    """

    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        user_id = message.from_user.id
        user_tag = message.from_user.username
        user_name = message.from_user.full_name
        if not check_user_exists(user_id):
            add_user_to_db(user_id, user_tag, user_name)
            msg = f"Пользователь {user_name} ({user_id}) добавлен в базу данных"
            write_user_log(msg)

        return await handler(message, *args, **kwargs)

    return wrapper
