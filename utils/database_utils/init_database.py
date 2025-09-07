import sqlite3

from config import BIRTHDAY_DATABASE


def init_database():
    """
    Инициализирует базу данных бота, проверяет существуют ли таблицы.
    Если нет, то создаёт их. Запускается при запуске бота.
    """
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Проверка и создание таблицы пользователей user
    cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id int primary key,
                user_tag str,
                user_name str,
                real_user_name str,
                cust_user_name str,
                user_day int,
                user_month int,
                user_year int,
                user_wishlist str,
                user_group str,
                user_subgroup str,
                is_approved bool,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Проверка и создание таблицы активности пользователей user_activity
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Индексы для ускорения выборок
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_ts ON user_activity(ts)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_ts ON user_activity(user_id, ts)")

    con.commit()
    cur.close()
    con.close()