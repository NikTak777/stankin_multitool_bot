from utils.database import get_user_info
from utils.date_utils import format_date
from utils.database_utils.friends import get_friends_info
from utils.database_utils.database_statistic import get_user_rank_by_activity, get_user_rank_by_days
from dataclasses import dataclass


def get_friend_profile_text(friend_id: int) -> str:
    user_info = get_user_info(friend_id) or {}

    day, month, year = user_info["user_day"], user_info["user_month"], user_info["user_year"]
    if not day or not month or not year:
        birthdate = "Отсутствует"
    else:
        birthdate = format_date(day, month, year)

    user_name = user_info["user_tag"]
    user_name = f"@{user_name}" if user_name else ""
    full_name = user_info["user_name"]

    wishlist = user_info["user_wishlist"] or "Отсутствует"
    group = user_info["user_group"] or "Отсутствует"
    subgroup = user_info["user_subgroup"] or "Отсутствует"
    subgroup = {"A": "А", "B": "Б"}.get(subgroup, subgroup)


    rank_activity = get_user_rank_by_activity(friend_id)
    rank_days = get_user_rank_by_days(friend_id)

    rank_activity_text = f"#{rank_activity}" if rank_activity > 0 else "Нет данных"
    rank_days_text = f"#{rank_days}" if rank_days > 0 else "Нет данных"

    text = (
        f"👤 Профиль {full_name} {user_name}\n\n"
        f"🎂 Дата рождения: {birthdate}\n"
        f"🎁 Вишлист: {wishlist}\n"
        f"🏫 Группа: {group}\n"
        f"📚 Подгруппа: {subgroup}\n\n"
        f"📊 Статистика:\n"
        f"🎯 Место в топе по действиям: {rank_activity_text}\n"
        f"📅 Место в топе по дням: {rank_days_text}"
    )

    return text


@dataclass(slots=True)
class FriendProfileResult:
    status: str
    index: int
    msg_to_user: str
    friend_id: int | None
    friend_name: str | None

def friend_profile_service(user_id: int, index: int) -> FriendProfileResult:
    pairs = get_friends_info(user_id)
    total = len(pairs)

    if total == 0:
        return FriendProfileResult(
            status="not_found",
            index=0,
            msg_to_user="❌ Профиль друга не найден",
            friend_id=None,
            friend_name=None
        )

    if index >= total: index = 0

    friend_id, friend_name = pairs[index]

    return FriendProfileResult(
        status="success",
        index=index,
        msg_to_user=get_friend_profile_text(friend_id),
        friend_id=friend_id,
        friend_name=friend_name
    )



