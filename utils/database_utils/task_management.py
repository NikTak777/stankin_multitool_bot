# utils/database_utils/task_management.py
import sqlite3
from datetime import datetime

from config import BIRTHDAY_DATABASE
from utils.logger import write_user_log


def get_task_status(task_name: str) -> bool:
    """Получает статус таска (включен/выключен)."""
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()
    
    cur.execute("""
        SELECT enabled FROM task_settings WHERE task_name = ?
    """, (task_name,))
    
    result = cur.fetchone()
    cur.close()
    con.close()
    
    # По умолчанию таск включен, если записи нет
    return bool(result[0]) if result else True


def set_task_status(task_name: str, enabled: bool) -> bool:
    """Устанавливает статус таска (включен/выключен)."""
    try:
        con = sqlite3.connect(BIRTHDAY_DATABASE)
        cur = con.cursor()
        
        cur.execute("""
            INSERT INTO task_settings (task_name, enabled, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(task_name) DO UPDATE SET
                enabled = ?,
                updated_at = ?
        """, (task_name, enabled, datetime.now(), enabled, datetime.now()))
        
        con.commit()
        cur.close()
        con.close()
        
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
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()
    
    cur.execute("SELECT task_name, enabled FROM task_settings")
    results = cur.fetchall()
    cur.close()
    con.close()
    
    return {task_name: bool(enabled) for task_name, enabled in results}