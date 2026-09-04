"""
Модуль для работы с подключением к PostgreSQL
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from utils.logger import write_user_log


@contextmanager
def get_db_connection():
    """
    Контекстный менеджер для подключения к PostgreSQL.
    Автоматически коммитит изменения при успешном выполнении или откатывает при ошибке.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        write_user_log(f"Ошибка подключения к БД: {e}")
        raise
    finally:
        if conn:
            conn.close()


def get_db_cursor(connection=None):
    """
    Получить курсор с RealDictCursor для удобной работы с результатами как со словарями.
    Если connection не передан, создается новое подключение.
    """
    if connection:
        return connection.cursor(cursor_factory=RealDictCursor)
    else:
        with get_db_connection() as conn:
            return conn.cursor(cursor_factory=RealDictCursor)

