"""
Инициализация PostgreSQL базы данных
"""
from utils.db_connection import get_db_connection
from utils.logger import write_user_log


def init_database():
    """
    Инициализирует PostgreSQL базу данных, проверяет существуют ли таблицы.
    Если нет, то создаёт их. Запускается при запуске бота.
    """
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            
            # Создание таблицы пользователей users
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
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
                    is_approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    friends TEXT,
                    schedule_notifications BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Создание индексов для таблицы users
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_group ON users(user_group)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_tag ON users(user_tag)
            """)
            
            # Создание таблицы активности пользователей user_activity
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event TEXT NOT NULL,
                    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для ускорения выборок
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_ts ON user_activity(ts)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_user_ts ON user_activity(user_id, ts)
            """)
            
            # Создание таблицы заявок в друзья friend_requests
            cur.execute("""
                CREATE TABLE IF NOT EXISTS friend_requests (
                    id SERIAL PRIMARY KEY,
                    sender_id BIGINT NOT NULL,
                    receiver_id BIGINT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sender_id, receiver_id)
                )
            """)
            
            # Создание таблицы предложений вишлиста wishlist_suggestions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wishlist_suggestions (
                    id SERIAL PRIMARY KEY,
                    sender_id BIGINT NOT NULL,
                    receiver_id BIGINT NOT NULL,
                    wishlist_text TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Создание таблицы настроек задач task_settings
            cur.execute("""
                CREATE TABLE IF NOT EXISTS task_settings (
                    task_name TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Инициализируем таски по умолчанию (все включены)
            default_tasks = [
                ('daily_schedule', True),
                ('birthday_notifications', True),
                ('new_year_greetings', True),
                ('schedule_notifications', True)
            ]
            
            for task_name, enabled in default_tasks:
                cur.execute("""
                    INSERT INTO task_settings (task_name, enabled)
                    VALUES (%s, %s)
                    ON CONFLICT (task_name) DO NOTHING
                """, (task_name, enabled))
            
            # Проверяем и добавляем недостающие столбцы
            ensure_columns(cur, "users")
            
            write_user_log("База данных PostgreSQL инициализирована успешно")
            
    except Exception as e:
        write_user_log(f"Ошибка при инициализации базы данных: {e}")
        raise


def ensure_columns(cursor, table_name: str):
    """
    Проверяет существующие столбцы таблицы и добавляет недостающие.
    :param cursor: psycopg2 cursor
    :param table_name: имя таблицы
    """
    # Получаем список существующих столбцов из information_schema
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s
    """, (table_name,))
    
    existing_columns = {row[0] for row in cursor.fetchall()}
    
    # Ожидаемые столбцы для таблицы users
    expected_columns = {
        "user_id": "BIGINT PRIMARY KEY",
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
        "is_approved": "BOOLEAN DEFAULT FALSE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "friends": "TEXT",
        "schedule_notifications": "BOOLEAN DEFAULT FALSE"
    }
    
    # Добавляем недостающие столбцы
    for column_name, column_def in expected_columns.items():
        if column_name not in existing_columns:
            # Для PRIMARY KEY столбцов пропускаем, так как они уже должны быть созданы
            if "PRIMARY KEY" not in column_def:
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
                    write_user_log(f"Добавлен столбец '{column_name}' в таблицу '{table_name}'")
                    
                    # Если добавляется schedule_notifications, устанавливаем FALSE для всех существующих пользователей
                    if column_name == "schedule_notifications":
                        cursor.execute(f"UPDATE {table_name} SET {column_name} = FALSE WHERE {column_name} IS NULL")
                        write_user_log(f"Установлено значение по умолчанию (FALSE) для столбца '{column_name}' у всех пользователей")
                except Exception as e:
                    write_user_log(f"Ошибка при добавлении столбца '{column_name}': {e}")
