# utils/database_utils/task_management.py
from datetime import datetime

from utils.db_connection import get_db_connection
from utils.logger import write_user_log


def get_task_status(task_name: str) -> bool:
    """Получает статус таска (включен/выключен)."""
    try:
        with get_db_connection() as con:
            cur = con.cursor()

            cur.execute("""
                        SELECT enabled FROM task_settings WHERE task_name = %s
            """, (task_name,))

            result = cur.fetchone()

            # По умолчанию таск включен, если записи нет
            return bool(result[0]) if result else True
    except Exception as e:
        write_user_log(f"Ошибка при получении статуса таска '{task_name}': {e}")
        return True  # По умолчанию включен при ошибке


def set_task_status(task_name: str, enabled: bool) -> bool:
    """Устанавливает статус таска (включен/выключен)."""
    try:
        with get_db_connection() as con:
            cur = con.cursor()

            cur.execute("""
                INSERT INTO task_settings (task_name, enabled, updated_at)
                    VALUES (%s, %s, %s)
                ON CONFLICT(task_name) DO UPDATE SET
                        enabled = %s,
                        updated_at = %s
            """, (task_name, enabled, datetime.now(), enabled, datetime.now()))

            status_text = "включен" if enabled else "выключен"
            write_user_log(f"Таск '{task_name}' {status_text}")
            return True
    except Exception as e:
        write_user_log(f"Ошибка при изменении статуса таска '{task_name}': {e}")
        return False


def toggle_task(task_name: str) -> bool:
    """Переключает статус таска (включен <-> выключен)."""
    current_status = get_task_status(task_name)
    new_status = not current_status
    return set_task_status(task_name, new_status)


def get_all_tasks_status() -> dict[str, bool]:
    """Получает статусы всех тасков."""
    try:
        with get_db_connection() as con:
            cur = con.cursor()

            cur.execute("SELECT task_name, enabled FROM task_settings")
            results = cur.fetchall()

            return {task_name: bool(enabled) for task_name, enabled in results}
    except Exception as e:
        write_user_log(f"Ошибка при получении статусов тасков: {e}")
        return {}
