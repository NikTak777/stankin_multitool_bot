from utils.db_connection import get_db_connection

def is_active_user_in_range(user_id: int, days_range: int, days_count: int):
    """
    Возвращает число активных дней из указанного диапазона,
    либо False если неправильно указаны параметры.
    """
    if days_range >= days_count:
        with get_db_connection() as con:
            cur = con.cursor()

            cur.execute("""
                SELECT COUNT(DISTINCT ts)
                FROM user_activity
                WHERE user_id = 
            """, (user_id, days_count, ))
            (n,) = cur.fetchone()

            return n or 0
    else:
        return False
