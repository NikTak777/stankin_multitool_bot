from datetime import datetime
from random import choices

from utils.database_utils.friends import get_list_friends
from utils.database_utils.contest import get_active_days_count
from utils.time import format_str_to_datetime, get_now_time
from utils.database import get_user_info, get_all_user_ids

START_DATE = format_str_to_datetime("04-09-2026")
END_DATE = format_str_to_datetime("13-09-2026")
ACTIVE_DAYS_COUNT = 3

"""
Условия конкурса:
1. Наличие номера группы в БД -> 3 дня активности по просмотру расписания;
2. Наличие трёх и более друзей с активностью 3 дня минимум по просмотру расписания (такие друзья называются активными).
Розыгрыш происходит среди тех, кто подходит под выше указанные условия.
Во время случайного выбора победителя каждый претендент имеет вес, равный количеству активных друзей:
- каждый активный друг засчитывается в 3 очка;
- каждый неактивный друге засчитывается в 1 очко;
Например, человек с 3 активными и 2 неактивными друзьями имеет вес в розыгрыше 3 * 3 + 2 * 1 = 11.
Ограничение: максимум засчитывается 10 неактивных друзей.
"""


def check_conditions(user_id: int) -> str:
    now = get_now_time()

    # 1. Проверка, начался ли период конкурса
    if now < START_DATE:
        delta = START_DATE - now
        total_seconds = int(delta.total_seconds())
        days = delta.days
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"До начала конкурса осталось: {days} дн. {hours} ч. {minutes} мин."
        return f"До начала конкурса осталось: {hours} ч. {minutes} мин."

    # 2. Проверка, закончился ли период конкурса
    if now > END_DATE:
        delta = now - END_DATE
        total_seconds = int(delta.total_seconds())
        days = delta.days
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"Конкурс закончился {days} дн. {hours} ч. {minutes} мин. назад"
        return f"Конкурс закончился {hours} ч. {minutes} мин. назад"

    # 3. Проверка на три дня активности пользователя
    info_msg = f"Вы пока не участвуете в розыгрыше:\n<b>условия конкурса ещё не выполнены!</b>\n\n"
    info_msg += f"Выполнение условий розыгрыша:\n"

    active_days = get_active_days_count(user_id, START_DATE, END_DATE)
    if active_days < ACTIVE_DAYS_COUNT:
        user_status = "❌"
    else:
        user_status = "✅"
    info_msg += f"{user_status} Ваша активность: {active_days} из {ACTIVE_DAYS_COUNT}\n"

    # 5. Список активности друзей
    friends: list[dict] = get_friends_activity(user_id)
    count_active_friends = 0
    count_inactive_friends = 0
    friends_list = "Сводка о ваших друзьях:\n"
    for friend in friends:
        count = friend['count']
        friend_status = "✅ Активен" if count >= 3 else "❌ Неактивен"
        friends_list += f"{friend_status} {get_user_info(friend['friend_id'])['user_name']}, активность {count} из {ACTIVE_DAYS_COUNT}\n"
        if friend['count'] >= 3:
            count_active_friends += 1
        else:
            count_inactive_friends += 1

        if (count_active_friends + count_inactive_friends) == 10:
            break

    friend_status = "✅" if count_active_friends >= 3 else "❌"

    info_msg += f"{friend_status} Активных друзей: {count_active_friends} из {ACTIVE_DAYS_COUNT}\n\n"

    info_msg += f"{friends_list}\n\n"

    win_weight: int = get_user_weight(count_active_friends, count_inactive_friends)

    info_msg += f"Ваше количество очков: {win_weight}\n"

    win_chance: float = get_win_chance(win_weight)

    info_msg += f"Ваш шанс победить: {win_chance}\n"

    return info_msg


def get_friends_activity(user_id: int) -> list[dict]:
    activity: list[dict] = []

    friends: list[int] = get_list_friends(user_id)
    for friend in friends:
        count: int = get_active_days_count(
            user_id=friend,
            start_date=START_DATE,
            end_date=END_DATE
        )

        activity.append(
            {
                "friend_id": friend,
                "count": count
            }
        )

    return sorted(activity, count)


def get_win_chance(win_weight: int) -> float:
    other_weight: int = 0
    users_list: list[int] = get_all_user_ids()
    for user_id in users_list:
        if get_active_days_count(user_id, START_DATE, END_DATE) >= ACTIVE_DAYS_COUNT:
            friends: list[dict] = get_friends_activity(user_id)
            count_active_friends: int = 0
            count_inactive_friends: int = 0
            for friend in friends:
                if friend['count'] >= 3:
                    count_active_friends += 1
                else:
                    count_inactive_friends += 1
            if count_active_friends >= 3:
                other_weight += get_user_weight(count_active_friends, count_inactive_friends)

    if other_weight == 0:
        return 0
    return win_weight / other_weight


def get_user_weight(count_active_friends: int, count_inactive_friends: int) -> int:
    user_weight: int = count_active_friends * 3 + min(count_inactive_friends, 10)
    return user_weight


def start_raffle():
    all_users: list[int] = get_all_user_ids()
    active_users: list[int] = []
    weight_users: list[int] = []

    for user_id in all_users:
        if get_active_days_count(user_id, START_DATE, END_DATE) >= ACTIVE_DAYS_COUNT:
            friends: list[dict] = get_friends_activity(user_id)
            count_active_friends: int = 0
            count_inactive_friends: int = 0
            for friend in friends:
                if friend['count'] >= 3:
                    count_active_friends += 1
                else:
                    count_inactive_friends += 1
            if count_active_friends >= 3:
                active_users.append(user_id)
                weight_users.append(get_user_weight(count_active_friends, count_inactive_friends))

    win_user_id: list[int] = choices(active_users, weights=weight_users, k=1)
    return win_user_id
