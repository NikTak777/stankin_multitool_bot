from datetime import datetime

from utils.db_connection import get_db_connection


def get_active_days_count(user_id: int, start_date: datetime, end_date: datetime, activity: str = "schedule") -> int:
    """
    Возвращает количество уникальных дней из указанного диапазона дат,
    в которые пользователь совершал целевую активность.
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT COUNT(DISTINCT DATE(ts + INTERVAL '3 hours'))
            FROM user_activity
            WHERE user_id = %s
            AND (ts + INTERVAL '3 hours') >= %s 
            AND (ts + INTERVAL '3 hours') <= %s
            AND event = %s
        """, (user_id, start_date, end_date, activity))

        result = cur.fetchone()
        return result[0] if result else 0


def get_winner_contest(activity: str = "contest") -> int:
    """Возвращает id последнего пользователя, кто получил выигрышную активность."""
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT user_id
            FROM user_activity
            WHERE event = %s
            ORDER BY ts DESC
            LIMIT 1
            
        """, (activity,))

        result = cur.fetchone()
        return result[0] if result else 0


def get_all_users_activity(start_date: datetime, end_date: datetime, activity: str = "schedule") -> dict[int, int]:
    """
    Возвращает словарь пользователей и количество дней
    просмотра расписания в указанный период времени.
    Возвращает словарь вида {user_id: active_days_count}
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT user_id, COUNT(DISTINCT DATE(ts + INTERVAL '3 hours'))
            FROM user_activity
            WHERE (ts + INTERVAL '3 hours') >= %s 
            AND (ts + INTERVAL '3 hours') <= %s
            AND event = %s
            GROUP BY user_id
        """, (start_date, end_date, activity))

        return {row[0]: row[1] for row in cur.fetchall()}
