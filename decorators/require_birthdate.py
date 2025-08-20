# decorators/require_birthdate.py
from functools import wraps
from utils.database import get_user_info
from utils.logger import write_user_log
from keyboards.birthdate_required import get_birthdate_required_keyboard


def require_birthdate(mode: str = "info"):
    messages = {
        "info": (
            "Информация не может быть выведена, так как вы не указали дату рождения.\n"
            "Пожалуйста, используйте команду /birthdate для создания аккаунта."
        ),
        "friend_wishlist": (
            "Вишлист не может быть выведен, так как вы не указали свою дату рождения.\n"
            "Пожалуйста, используйте команду /birthdate для создания аккаунта."
        ),
        "user_wishlist": (
            "Вишлист не может быть введён, так как вы не указали дату рождения.\n"
            "Пожалуйста, используйте команду /birthdate для создания аккаунта."
        )
    }

    def decorator(func):
        @wraps(func)
        async def wrapper(user, message_obj, *args, is_callback=False, **kwargs):
            user_id = user.id
            user_info = get_user_info(user_id)

            if not user_info or not (user_info.get("user_day") and user_info.get("user_month") and user_info.get("user_year")):
                text = messages.get(mode, messages["info"])
                if is_callback:
                    await message_obj.edit_text(text, reply_markup=get_birthdate_required_keyboard())
                else:
                    await message_obj.answer(text, reply_markup=get_birthdate_required_keyboard())

                write_user_log(
                    f"Пользователь {user.full_name} ({user_id}) не может выполнить действие '{mode}'. "
                    f"Дата рождения не указана"
                )
                return
            return await func(user, message_obj, *args, is_callback=is_callback, **kwargs)

        return wrapper

    return decorator
