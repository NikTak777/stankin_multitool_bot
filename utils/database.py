import pytz
from datetime import datetime, timedelta

from utils.db_connection import get_db_connection

tz_moscow = pytz.timezone("Europe/Moscow")  # Часовой пояс Москвы


def set_user_birthdate(user_id, user_day, user_month, user_year):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        existing_user = cur.fetchone()

        if existing_user:
            cur.execute("UPDATE users SET user_day = %s, user_month = %s, user_year = %s WHERE user_id = %s",
                        (user_day, user_month, user_year, user_id))
        else:
            cur.execute("INSERT INTO users (user_id, user_day, user_month, user_year, is_approved) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, user_day, user_month, user_year, False))


def check_users():
    with get_db_connection() as con:
        cur = con.cursor()

        now = datetime.now(tz=tz_moscow)
        today_day = now.day
        today_month = now.month

        cur.execute("SELECT user_id FROM users WHERE user_day = %s AND user_month = %s",
                    (today_day, today_month))

        birthdays = cur.fetchall()

        return [str(b[0]) for b in birthdays]


def check_users_in_7_days():
    now = datetime.now(tz=tz_moscow)  # Текущая дата и время в Московском часовом поясе
    target_date = now + timedelta(days=7)  # Дата через 7 дней

    target_day = target_date.day
    target_month = target_date.month

    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute(
            "SELECT user_id FROM users WHERE user_day = %s AND user_month = %s",
            (target_day, target_month)
        )

        birthdays = cur.fetchall()

        return [str(b[0]) for b in birthdays]


def get_real_user_name(user_id):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT 
                CASE 
                    WHEN cust_user_name IS NOT NULL AND cust_user_name != '' 
                    THEN cust_user_name
                    ELSE user_name 
                END AS final_name 
            FROM users 
            WHERE user_id = %s
        """, (user_id,))

        result = cur.fetchone()

        return result[0] if result else None


def check_user_exists(user_id):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()

        return result is not None


def update_cust_user_name(user_id, cust_user_name):
    if not check_user_exists(user_id):
        return None  # Если пользователя нет, возвращаем None

    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("UPDATE users SET cust_user_name = %s WHERE user_id = %s", (cust_user_name, user_id))


def update_user_name(user_id: int, user_name: str, full_name: str) -> bool:
    """
    Обновляет user_name (Telegram full_name/username) для пользователя в БД.

    :param user_id: Telegram user_id
    :param user_name: Новый user_name
    :param full_name: Новый full_name
    :return: True, если обновление прошло успешно, иначе False
    """
    if not check_user_exists(user_id):
        return False  # Если пользователя нет, ничего не делаем

    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("UPDATE users SET user_tag = %s, user_name = %s WHERE user_id = %s", (user_name, full_name, user_id))
        return cur.rowcount > 0


def update_user_wishlist(user_id, user_wishlist):
    if not check_user_exists(user_id):
        return None

    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("UPDATE users SET user_wishlist = %s WHERE user_id = %s", (user_wishlist, user_id))


def update_is_approved(user_id, is_approved):
    if not check_user_exists(user_id):
        return None

    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("UPDATE users SET is_approved = %s WHERE user_id = %s", (is_approved, user_id))


def get_user_info(user_id):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute(
            "SELECT user_tag, user_name, real_user_name, cust_user_name,"
            "user_day, user_month, user_year, user_wishlist, user_group, user_subgroup, is_approved, schedule_notifications FROM users WHERE user_id = %s",
            (user_id,)
        )
        result = cur.fetchone()

        if result:
            return {
                "user_tag": result[0],
                "user_name": result[1],
                "real_user_name": result[2],
                "cust_user_name": result[3],
                "user_day": result[4],
                "user_month": result[5],
                "user_year": result[6],
                "user_wishlist": result[7],
                "user_group": result[8],
                "user_subgroup": result[9],
                "is_approved": result[10],
                "schedule_notifications": result[11] if result[11] is not None else False
            }
        return None


def get_all_user_ids():
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        return [str(user[0]) for user in users]


def get_user_wishlist(user_tag):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT user_name, user_wishlist FROM users WHERE user_tag = %s", (user_tag,))
        result = cur.fetchone()

        if not result:
            return "not_found"

        user_name, wishlist = result

        if not wishlist:
            return user_name, "no_wishlist"

        return user_name, wishlist


def set_user_group_subgroup(user_id, user_group, user_subgroup):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("UPDATE users SET user_group = %s, user_subgroup = %s WHERE user_id = %s",
                    (user_group, user_subgroup, user_id))


def add_user_to_db(user_id, user_tag, user_name):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("INSERT INTO users (user_id, user_tag, user_name) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
                    (user_id, user_tag, user_name))


def get_users_by_group(group_name: str) -> list[dict]:
    """
    Возвращает актуальный список студентов группы из базы данных.

    Параметры:
        group_name (str): Название группы для поиска

    Возвращает:
        list[dict]: Список словарей с ключами 'id' и 'name'
        Пример: [{'id': 123, 'name': 'Иван Иванов', 'approved': True}, ...]
    """
    students = []

    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT user_id, real_user_name, user_name, is_approved "
                "FROM users WHERE user_group = %s",
                (group_name,)
            )

            for row in cur.fetchall():
                real_name = row[2] or row[1] or "Неизвестный"  # real_user_name или user_name
                students.append({
                    'id': row[0],  # user_id
                    'name': real_name,
                    'approved': bool(row[3])  # is_approved
                })
    except Exception as e:
        print(f"Ошибка получения студентов: {e}")
    return students


def update_real_user_name(user_id, real_user_name):
    """Обновляет реальное имя пользователя. Возвращает True при успешном обновлении."""
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute(
                "UPDATE users SET real_user_name = %s WHERE user_id = %s",
                (real_user_name, user_id)
            )
            return cur.rowcount > 0  # True если была изменена хотя бы одна строка
    except Exception as e:
        print(f"Ошибка обновления имени для пользователя {user_id}: {e}")
        return False


def toggle_user_approval(user_id: int) -> bool:
    """Переключает статус разрешения поздравлений для пользователя"""
    try:
        with get_db_connection() as con:
            cur = con.cursor()

            # Получаем текущее состояние
            cur.execute(
                "SELECT is_approved FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            if not result:
                return False
            current_status = result[0]

            # Устанавливаем противоположное значение
            new_status = not current_status

            cur.execute(
                "UPDATE users SET is_approved = %s WHERE user_id = %s",
                (new_status, user_id)
            )
            return new_status
    except Exception as e:
        print(f"Ошибка переключения статуса: {e}")
        return False


def get_approval_status(user_id: int) -> bool:
    """Возвращает текущий статус разрешения поздравлений"""
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT is_approved FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            return bool(result[0]) if result else False
    except Exception as e:
        print(f"Ошибка получения статуса: {e}")
        return False


def toggle_schedule_notifications(user_id: int) -> bool:
    """Переключает статус рассылки расписания для пользователя"""
    try:
        with get_db_connection() as con:
            cur = con.cursor()

            # Получаем текущее состояние
            cur.execute(
                "SELECT schedule_notifications FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            current_status = bool(result[0]) if result and result[0] is not None else False

            # Устанавливаем противоположное значение
            new_status = not current_status

            cur.execute(
                "UPDATE users SET schedule_notifications = %s WHERE user_id = %s",
                (new_status, user_id)
            )
            return new_status
    except Exception as e:
        print(f"Ошибка переключения статуса рассылки расписания: {e}")
        return False


def get_schedule_notifications_status(user_id: int) -> bool:
    """Возвращает текущий статус рассылки расписания"""
    try:
        with get_db_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT schedule_notifications FROM users WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()
            return bool(result[0]) if result and result[0] is not None else False
    except Exception as e:
        print(f"Ошибка получения статуса рассылки расписания: {e}")
        return False


def clear_users():
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("DELETE FROM users")


def get_id_from_username(username):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT user_id FROM users WHERE user_tag = %s", (username,))
        result = cur.fetchone()

        if not result:
            return "not_found"

        return result


def check_user_by_username(username: str) -> bool:
    """
    Проверяет, существует ли пользователь с данным username в таблице users.
    :param username: username без @
    :return: True, если пользователь есть в базе, иначе False
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT 1 FROM users WHERE user_tag = %s", (username,))
        result = cur.fetchone()

        return result is not None
