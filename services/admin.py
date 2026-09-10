from utils.database import get_real_user_name
from utils.database_utils.database_statistic import get_users_count, count_active_users, count_new_users, get_last_active_users, get_top_active_users, get_top_users_by_days
from utils.database_utils.task_management import toggle_task, get_task_status

def get_summary_panel(user_id: int) -> str:
    full_name = get_real_user_name(user_id)

    # Получаем топ-10 последних пользователей
    last_users = get_last_active_users(10)
    last_users_text = "\n".join([
        f"{i + 1}. {u['user_name']} @{u['user_tag']}"
        for i, u in enumerate(last_users)
    ])

    # Получаем топ-5 активных пользователей
    top_users = get_top_active_users(5)
    top_users_text = "\n".join([
        f"{i + 1}. {u['user_name']} @{u['user_tag']} ({u['activity_count']} событий)"
        for i, u in enumerate(top_users)
    ])

    # Получаем топ-5 пользователей по количеству дней использования
    top_days_users = get_top_users_by_days(5)
    top_days_text = "\n".join([
        f"{i + 1}. {u['user_name']} @{u['user_tag']} ({u['days_count']} дней)"
        for i, u in enumerate(top_days_users)
    ])

    text = (
        f"Привет, {full_name}!\n"
        "Это панель управления ботом.\n\n"
        f"👥 Количество пользователей: {get_users_count()}\n"
        f"👥 Количество новых пользователей за неделю: {count_new_users(7)}\n"
        f"👥 Количество уникальных пользователей за неделю: {count_active_users(7)}\n"
        f"👥 Последние активные пользователи:\n{last_users_text}\n\n"
        f"🏆 Топ-5 самых активных пользователей за всё время:\n{top_users_text}\n\n"
        f"📅 Топ-5 пользователей по количеству дней использования:\n{top_days_text}"
    )

    return text


def get_activity_panel() -> str:
    # Получение топ-30 активных пользователей
    top_users = get_top_active_users(30)
    top_users_text = "\n".join([
        f"{i + 1}. {u['user_name']} @{u['user_tag']} ({u['activity_count']} событий)"
        for i, u in enumerate(top_users)
    ])

    text =f"🏆 Топ-30 самых активных за всё время:\n{top_users_text}"

    return text


def get_usability_panel() -> str:
    # Получение топ-30 пользователей по количеству дней использования
    top_days_users = get_top_users_by_days(30)
    top_days_text = "\n".join([
        f"{i+1}. {u['user_name']} @{u['user_tag']} ({u['days_count']} дней)"
        for i, u in enumerate(top_days_users)
    ])

    text =f"🏆 Топ-30 пользователей по количеству дней использования:\n{top_days_text}"

    return text


TASK_NAMES = {
    "daily_schedule": "📅 Ежедневная рассылка расписания",
    "birthday_notifications": "🎂 Уведомления о днях рождения",
    "new_year_greetings": "🎄 Новогодние поздравления",
    "schedule_notifications": "⏰ Уведомления о расписании занятий"
}

def get_task_panel() -> str:
    tasks_status = {}
    for task_key in TASK_NAMES.keys():
        tasks_status[task_key] = get_task_status(task_key)

    status_lines = []
    for task_key, task_display_name in TASK_NAMES.items():
        status = tasks_status[task_key]
        status_icon = "✅" if status else "❌"
        status_lines.append(f"{status_icon} {task_display_name}: {'Вкл.' if status else 'Выкл.'}")

    text = (
            f"⚙️ Меню управления тасками\n\n"
            "Нажмите кнопку, чтобы переключить работу таски:\n\n" +
            "\n".join(status_lines)
    )
    return text