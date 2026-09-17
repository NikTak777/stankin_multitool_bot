from utils.database import get_user_info
from utils.date_utils import format_date


def get_profile_info_text(user_id: int) -> str:
    user_info = get_user_info(user_id)

    day = user_info.get("user_day")
    month = user_info.get("user_month")
    year = user_info.get("user_year")

    if not day or not month or not year:
        birthdate = "Отсутствует"
    else:
        birthdate = format_date(day, month, year)

    nick_name = user_info["cust_user_name"] or "Отсутствует"
    user_name = user_info["user_tag"]
    user_name = f"@{user_name}" if user_name else ""
    full_name = user_info["user_name"]

    wishlist = user_info["user_wishlist"] or "Отсутствует"
    group = user_info["user_group"] or "Отсутствует"
    subgroup = user_info["user_subgroup"] or "Отсутствует"
    subgroup = {"A": "А", "B": "Б"}.get(subgroup, subgroup)

    schedule_notifications = user_info.get("schedule_notifications", 0)
    schedule_status = "Вкл." if schedule_notifications else "Выкл."

    text = (
        f"📌 Информация о Вашем аккаунте:\n\n"
        f"👤 Имя пользователя: {full_name} {user_name}\n"
        f"🏷 Никнейм: {nick_name}\n"
        f"🎂 Дата рождения: {birthdate}\n"
        f"🎁 Вишлист: {wishlist}\n"
        f"🏫 Группа: {group}\n"
        f"📚 Подгруппа: {subgroup}\n"
        f"📬 Рассылка расписания: {schedule_status}"
    )

    return text