import sqlite3

from config import BIRTHDAY_DATABASE

from utils.logger import write_user_log

# Словарь всех атрибутов таблицы user {"name_column": "type"}
expected_columns = {
    "user_id": "INTEGER PRIMARY KEY",
    "user_tag": "TEXT",
    "user_name": "TEXT",
    "real_user_name": "TEXT",
    "cust_user_name": "TEXT",
    "user_day": "INTEGER",
    "user_month": "INTEGER",
    "user_year": "INTEGER",
    "user_wishlist": "TEXT",
    "user_group": "TEXT",
    "user_subgroup": "TEXT",
    "is_approved": "BOOLEAN",
    "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
    "friends": "TEXT"
}


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
                user_id INTEGER PRIMARY KEY,
                user_tag TEXT,
                user_name TEXT,
                real_user_name TEXT,
                cust_user_name TEXT,
                user_day INTEGER,
                user_month INTEGER,
                user_year INTEGER,
                user_wishlist TEXT,
                user_group TEXT,
                user_subgroup TEXT,
                is_approved BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                friends TEXT
            )
        """)

    ensure_columns(cur, "users", expected_columns)

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS friend_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',  -- Статусы: 'pending', 'accepted', 'declined'
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.commit()
    cur.close()
    con.close()


def ensure_columns(cursor, table_name, expected_columns: dict):
    """
    Проверяет существующие столбцы таблицы и добавляет недостающие.
    :param cursor: sqlite3.Cursor
    :param table_name: имя таблицы
    :param expected_columns: словарь {имя_столбца: тип_и_опции}
    """
    # Получаем список существующих столбцов
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Добавляем недостающие
    for column_name, column_def in expected_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
            write_user_log(f"Добавлен столбец '{column_name}' в таблицу '{table_name}'")