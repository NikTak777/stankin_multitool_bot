from datetime import datetime
from random import choices
from operator import itemgetter

from utils.database_utils.friends import get_list_friends
from utils.database_utils.contest import get_active_days_count
from utils.time import format_str_to_datetime, get_now_time
from utils.database import get_user_info, get_all_user_ids
from utils.database_utils.database_statistic import log_user_activity

START_DATE = format_str_to_datetime("18-09-2026")
END_DATE = format_str_to_datetime("28-09-2026")
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
        info_msg += f"❌ Ваша активность: невыполнена ({active_days} из {ACTIVE_DAYS_COUNT} дн.)\n"
    else:
        info_msg += f"✅ Ваша активность: выполнена ({active_days} из {ACTIVE_DAYS_COUNT} дн.)\n"

    # 5. Список активности друзей
    friends: list[dict] = get_friends_activity(user_id)
    count_active_friends = 0
    count_inactive_friends = 0
    friends_list_text = "Сводка о ваших друзьях:\n"
    for friend in friends:
        friend_name: str = get_user_info(friend['friend_id'])['user_name']
        count: int = friend['count']
        if friend['count'] >= 3:
            friends_list_text += f"⭐️ {friend_name}: активен ({friend['count']} из {ACTIVE_DAYS_COUNT} дн.)\n"
            count_active_friends += 1
        else:
            friends_list_text += f"💤 {friend_name}: мало активности ({friend['count']} из {ACTIVE_DAYS_COUNT} дн.)\n"
            count_inactive_friends += 1

    if count_active_friends >= 3:
        info_msg += f"✅ Активных друзей: выполнено ({count_active_friends} из {ACTIVE_DAYS_COUNT} чел.)\n\n"
    else:
        info_msg += f"❌ Активных друзей: невыполнено ({count_active_friends} из {ACTIVE_DAYS_COUNT} чел.)\n\n"

    info_msg += f"{friends_list_text}\n\n"

    win_weight: int = get_user_weight(count_active_friends, count_inactive_friends)
    info_msg += f"Ваше количество очков: {win_weight}\n"

    win_chance, top_percent = get_contest_stats(win_weight)
    info_msg += f"🎯 Текущая вероятность победы: {win_chance}%\n"
    info_msg += f"📈 Ваш статус: Вы входите в Топ-{top_percent}% участников с наивысшими шансами!\n"

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

    return sorted(activity, key=itemgetter("count"), reverse=True)


def get_contest_stats(user_weight: int) -> tuple[float, int]:
    all_eligible_weights: list[int] = []
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
                weight = get_user_weight(count_active_friends, count_inactive_friends)
                all_eligible_weights.append(weight)

    total_weight = sum(all_eligible_weights)
    if total_weight == 0:
        return 0.0, 100

    win_chance = (user_weight / total_weight) * 100

    total_eligible = len(all_eligible_weights)
    better_users = sum(1 for w in all_eligible_weights if w > user_weight)

    top_percent = int((better_users / total_eligible) * 100)
    if top_percent == 0:
        top_percent = 1

    return round(win_chance, 2), top_percent


def get_user_weight(count_active_friends: int, count_inactive_friends: int) -> int:
    user_weight: int = count_active_friends * 3 + min(count_inactive_friends, 10)
    return user_weight


def start_raffle() -> int:
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

    win_user_id: int = (choices(active_users, weights=weight_users, k=1))[0]
    log_user_activity(win_user_id, "contest_1")
    return win_user_id


def get_all_contest_stats() -> str:
    all_users: list[int] = get_all_user_ids()
    eligible_users: list[dict] = []
    total_weight: int = 0

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
                weight = get_user_weight(count_active_friends, count_inactive_friends)
                total_weight += weight

                user_name = get_user_info(user_id).get('user_name', f"ID {user_id}")

                eligible_users.append({
                    "name": user_name,
                    "weight": weight
                })

    if not eligible_users:
        return "😔 Пока нет участников, выполнивших все условия конкурса."

    for user in eligible_users:
        user['chance'] = (user['weight'] / total_weight) * 100

    eligible_users.sort(key=itemgetter("chance"), reverse=True)

    text_lines = ["🏆 Рейтинг участников розыгрыша:\n"]

    for i, user in enumerate(eligible_users, start=1):
        chance_str = f"{user['chance']:.2f}%"
        text_lines.append(f"{i}. {user['name']} — {chance_str}")

    return "\n".join(text_lines)