# services/other_profile_service.py

from utils.date_utils import format_date


def get_own_profile_info(user_info) -> str:
    day = user_info.get("user_day")
    month = user_info.get("user_month")
    year = user_info.get("user_year")

    wishlist = user_info.get("user_wishlist") or "Отсутствует"
    group = user_info.get("user_group") or "Отсутствует"
    subgroup = user_info.get("user_subgroup") or "Отсутствует"
    subgroup = {"A": "А", "B": "Б"}.get(subgroup, subgroup)

    bday_str = format_date(day, month, year)

    return ("Хм, вы ввели свой собственный тег. Пытаетесь проверить сами себя? 😉\n"
            "Ваш профиль:\n\n"
            f"🎂 Дата рождения: {bday_str}\n"
            f"🎁 Вишлист: {wishlist}\n"
            f"🏫 Группа: {group}\n"
            f"📚 Подгруппа: {subgroup}"
            )


def other_user_not_found(user_name: str) -> str:
    return f"Пользователь с тегом @{user_name} не найден."


def other_profile_info(user_info) -> str:
    day = user_info.get("user_day")
    month = user_info.get("user_month")
    year = user_info.get("user_year")

    full_name = user_info.get("user_name")
    wishlist = user_info.get("user_wishlist") or "Отсутствует"
    group = user_info.get("user_group") or "Отсутствует"
    subgroup = user_info.get("user_subgroup") or "Отсутствует"
    subgroup = {"A": "А", "B": "Б"}.get(subgroup, subgroup)

    bday_str = format_date(day, month, year)

    return (
        f"👤 Профиль {full_name}\n\n"
        f"🎂 Дата рождения: {bday_str}\n"
        f"🎁 Вишлист: {wishlist}\n"
        f"🏫 Группа: {group}\n"
        f"📚 Подгруппа: {subgroup}"
    )
