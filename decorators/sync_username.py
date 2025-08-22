from functools import wraps
from utils.database import update_user_name, get_user_info

def sync_username(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        tg_username = event.from_user.username
        tg_fullname = event.from_user.full_name

        user_info = get_user_info(user_id)
        db_username = user_info.get("user_tag")
        db_fullname = user_info.get("user_name")

        # Если ник изменился → обновляем в БД
        if tg_username != db_username or tg_fullname != db_fullname:
            update_user_name(user_id, tg_username, tg_fullname)

        return await handler(event, *args, **kwargs)
    return wrapper
