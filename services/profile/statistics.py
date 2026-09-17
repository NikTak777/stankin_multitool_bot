from utils.database_utils.database_statistic import (
    get_user_rank_by_activity,
    get_user_rank_by_days,
    get_user_statistics
)


def get_user_statistics_text(user_id: int) -> str:
    stats = get_user_statistics(user_id)
    rank_activity = get_user_rank_by_activity(user_id)
    rank_days = get_user_rank_by_days(user_id)

    rank_activity_text = f"#{rank_activity}" if rank_activity > 0 else "Нет данных"
    rank_days_text = f"#{rank_days}" if rank_days > 0 else "Нет данных"

    text = (
        f"📊 Ваша статистика:\n\n"
        f"🎯 Место в топе по количеству действий: {rank_activity_text} ({stats['total_actions']} действий)\n"
        f"📅 Место в топе по количеству дней: {rank_days_text} ({stats['days_count']} дней)\n"
        f"📈 Среднее количество действий в день: {stats['avg_actions_per_day']}\n"
        f"⏱ Длительность использования: {stats['days_since_first']} дней"
    )

    return text