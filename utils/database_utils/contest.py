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
            SELECT COUNT(DISTINCT DATE(ts))
            FROM user_activity
            WHERE user_id = %s
            AND ts >= %s 
            AND ts <= %s
            AND event = %s
        """, (user_id, start_date, end_date, activity))

        result = cur.fetchone()
        return result[0] if result else 0