# utils/database_utils/database_statistic.py
import sqlite3

from config import BIRTHDAY_DATABASE


def get_users_count() -> int:
    """Возвращает количество пользователей (строк) в таблице users."""
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    result = cur.fetchone()

    cur.close()
    con.close()

    return result[0] if result else 0


def log_user_activity(user_id: int, event: str) -> None:
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()
    cur.execute("INSERT INTO user_activity (user_id, event) VALUES (?, ?)", (user_id, event))
    con.commit(); cur.close(); con.close()


def count_active_users(days: int) -> int:
    """
    Возвращает количество уникальных пользователей,
    которые проявляли активность за последние N дней.
    """
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT COUNT(DISTINCT user_id)
        FROM user_activity
        WHERE ts >= datetime('now', ?)
    """, (f'-{days} days',))
    (n,) = cur.fetchone()

    cur.close()
    con.close()
    return n or 0


def count_new_users(days: int) -> int:
    """
    Возвращает количество пользователей,
    которые зарегистрировались за последние N дней.
    """
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE created_at >= datetime('now', ?)
    """, (f'-{days} days',))

    (n,) = cur.fetchone()
    cur.close()
    con.close()
    return n or 0


def get_last_users(limit: int) -> list[dict]:
    """
    Возвращает список последних зарегистрированных пользователей.
    limit — сколько пользователей показать (по дате регистрации).
    """
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT user_id, user_tag, user_name, created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    con.close()

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
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT user_id, user_tag, user_name, created_at
        FROM users
        WHERE created_at >= datetime('now', ?)
        ORDER BY created_at DESC
    """, (f'-{days} days',))

    rows = cur.fetchall()
    cur.close()
    con.close()

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
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT u.user_id, u.user_tag, u.user_name, MAX(a.ts) as last_active
        FROM user_activity a
        JOIN users u ON u.user_id = a.user_id
        GROUP BY u.user_id
        ORDER BY last_active DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    cur.close()
    con.close()

    return [
        {
            "user_id": row[0],
            "user_tag": row[1],
            "user_name": row[2],
            "last_active": row[3],
        }
        for row in rows
    ]