# utils/database_utils/database_statistic.py
from datetime import datetime, timedelta

from utils.db_connection import get_db_connection


def get_users_count() -> int:
    """Возвращает количество пользователей (строк) в таблице users."""
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        result = cur.fetchone()

        return result[0] if result else 0


def log_user_activity(user_id: int, event: str) -> None:
    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute("INSERT INTO user_activity (user_id, event) VALUES (%s, %s)", (user_id, event))


def count_active_users(days: int) -> int:
    """
    Возвращает количество уникальных пользователей,
    которые проявляли активность за последние N дней.
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT COUNT(DISTINCT user_id)
            FROM user_activity
            WHERE ts >= CURRENT_TIMESTAMP - make_interval(days => %s)
        """, (days,))
        (n,) = cur.fetchone()

        return n or 0


def count_new_users(days: int) -> int:
    """
    Возвращает количество пользователей,
    которые зарегистрировались за последние N дней.
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= CURRENT_TIMESTAMP - make_interval(days => %s)
        """, (days,))

        (n,) = cur.fetchone()
        return n or 0


def get_last_users(limit: int) -> list[dict]:
    """
    Возвращает список последних зарегистрированных пользователей.
    limit — сколько пользователей показать (по дате регистрации).
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT user_id, user_tag, user_name, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

        return [
            {
                "user_id": row[0],
                "user_tag": row[1],
                "user_name": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]


def get_users_last_days(days: int) -> list[dict]:
    """
    Возвращает список пользователей,
    которые зарегистрировались за последние N дней.
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT user_id, user_tag, user_name, created_at
            FROM users
            WHERE created_at >= CURRENT_TIMESTAMP - make_interval(days => %s)
            ORDER BY created_at DESC
        """, (days,))

        rows = cur.fetchall()

        return [
            {
                "user_id": row[0],
                "user_tag": row[1],
                "user_name": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]


def get_last_active_users(limit: int) -> list[dict]:
    """
    Возвращает список последних активных пользователей.
    limit — сколько последних уникальных пользователей вернуть.
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT u.user_id, u.user_tag, u.user_name, MAX(a.ts) as last_active
            FROM user_activity a
            JOIN users u ON u.user_id = a.user_id
            GROUP BY u.user_id
            ORDER BY last_active DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

        return [
            {
                "user_id": row[0],
                "user_tag": row[1],
                "user_name": row[2],
                "last_active": row[3],
            }
            for row in rows
        ]


def get_top_active_users(limit: int = 5) -> list[dict]:
    """
    Возвращает топ-N самых активных пользователей за всё время.
    Сортировка по количеству событий активности (убывание).
    
    :param limit: Количество пользователей для возврата (по умолчанию 5)
    :return: Список словарей с ключами: user_id, user_name, activity_count
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT 
                u.user_id,
                COALESCE(u.real_user_name, u.user_name, 'Неизвестный') as user_name,
                u.user_tag,
                COUNT(a.id) as activity_count
            FROM user_activity a
            JOIN users u ON u.user_id = a.user_id
            GROUP BY u.user_id
            ORDER BY activity_count DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

        return [
            {
                "user_id": row[0],
                "user_name": row[1],
                "user_tag": row[2],
                "activity_count": row[3],
            }
            for row in rows
        ]


def get_top_users_by_days(limit: int = 5) -> list[dict]:
    """
    Возвращает топ-N пользователей по количеству дней использования бота.
    Считается количество уникальных дней, когда пользователь был активен.
    
    :param limit: Количество пользователей для возврата (по умолчанию 5)
    :return: Список словарей с ключами: user_id, user_name, days_count
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT 
                u.user_id,
                COALESCE(u.real_user_name, u.user_name, 'Неизвестный') as user_name,
                u.user_tag,
                COUNT(DISTINCT DATE(a.ts)) as days_count
            FROM user_activity a
            JOIN users u ON u.user_id = a.user_id
            GROUP BY u.user_id
            ORDER BY days_count DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

        return [
            {
                "user_id": row[0],
                "user_name": row[1],
                "user_tag": row[2],
                "days_count": row[3],
            }
            for row in rows
        ]


def get_user_rank_by_activity(user_id: int) -> int:
    """
    Возвращает место пользователя в топе по количеству действий.
    :param user_id: ID пользователя
    :return: Место в рейтинге (1 = первое место) или 0, если пользователь не найден
    """
    with get_db_connection() as con:
        cur = con.cursor()

        # Получаем всех пользователей с их количеством действий, отсортированных по убыванию
        cur.execute("""
            SELECT 
                u.user_id,
                COUNT(a.id) as activity_count
            FROM user_activity a
            JOIN users u ON u.user_id = a.user_id
            GROUP BY u.user_id
            ORDER BY activity_count DESC
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            return 0
        
        # Ищем позицию пользователя в отсортированном списке
        rank = 0
        for idx, (uid, count) in enumerate(rows, start=1):
            if uid == user_id:
                rank = idx
                break
        
        return rank


def get_user_rank_by_days(user_id: int) -> int:
    """
    Возвращает место пользователя в топе по количеству дней использования.
    :param user_id: ID пользователя
    :return: Место в рейтинге (1 = первое место) или 0, если пользователь не найден
    """
    with get_db_connection() as con:
        cur = con.cursor()

        # Получаем всех пользователей с их количеством дней, отсортированных по убыванию
        cur.execute("""
            SELECT 
                u.user_id,
                COUNT(DISTINCT DATE(a.ts)) as days_count
            FROM user_activity a
            JOIN users u ON u.user_id = a.user_id
            GROUP BY u.user_id
            ORDER BY days_count DESC
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            return 0
        
        # Ищем позицию пользователя в отсортированном списке
        rank = 0
        for idx, (uid, count) in enumerate(rows, start=1):
            if uid == user_id:
                rank = idx
                break
        
        return rank


def get_user_statistics(user_id: int) -> dict:
    """
    Возвращает полную статистику пользователя.
    :param user_id: ID пользователя
    :return: Словарь со статистикой
    """
    with get_db_connection() as con:
        cur = con.cursor()

        # Общее количество действий
        cur.execute("SELECT COUNT(*) FROM user_activity WHERE user_id = %s", (user_id,))
        total_actions = cur.fetchone()[0] or 0

        # Количество дней использования
        cur.execute("SELECT COUNT(DISTINCT DATE(ts)) FROM user_activity WHERE user_id = %s", (user_id,))
        days_count = cur.fetchone()[0] or 0

        # Первая и последняя активность
        cur.execute("""
            SELECT MIN(ts), MAX(ts) 
            FROM user_activity 
            WHERE user_id = %s
        """, (user_id,))
        first_last = cur.fetchone()
        first_active = first_last[0] if first_last and first_last[0] else None
        last_active = first_last[1] if first_last and first_last[1] else None

        # Среднее количество действий в день
        avg_actions_per_day = round(total_actions / days_count, 1) if days_count > 0 else 0

        # Длительность использования (дней с первого использования)
        days_since_first = 0
        if first_active:
            # Вычисляем разницу в днях между текущей датой и первой активностью
            cur.execute("""
                SELECT EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - %s)) / 86400
            """, (first_active,))
            result = cur.fetchone()
            days_since_first = int(result[0]) if result and result[0] else 0

        return {
            "total_actions": total_actions,
            "days_count": days_count,
            "avg_actions_per_day": avg_actions_per_day,
            "days_since_first": days_since_first,
            "first_active": first_active,
            "last_active": last_active
        }
