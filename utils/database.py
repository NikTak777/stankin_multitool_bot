import sqlite3
import pytz
from datetime import datetime, timedelta

from config import BIRTHDAY_DATABASE

tz_moscow = pytz.timezone("Europe/Moscow") # Часовой пояс Москвы


def set_user_birthdate(user_id, user_day, user_month, user_year):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = cur.fetchone()

    if existing_user:
        cur.execute("UPDATE users SET user_day = ?, user_month = ?, user_year = ? WHERE user_id = ?",
                    (user_day, user_month, user_year, user_id))
    else:
        cur.execute("INSERT INTO users (user_id, user_day, user_month, user_year, is_approved) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, user_day, user_month, user_year))

    con.commit()
    cur.close()
    con.close()

def check_users():
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    now = datetime.now(tz=tz_moscow)
    today_day = now.day
    today_month = now.month

    cur.execute("SELECT user_id FROM users WHERE user_day = ? AND user_month = ?",
                (today_day, today_month))

    birthdays = cur.fetchall()

    cur.close()
    con.close()
    return [str(b[0]) for b in birthdays]


def check_users_in_7_days():

    now = datetime.now(tz=tz_moscow)  # Текущая дата и время в Московском часовом поясе
    target_date = now + timedelta(days=7)  # Дата через 7 дней

    target_day = target_date.day
    target_month = target_date.month

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_day = ? AND user_month = ?",
        (target_day, target_month)
    )

    birthdays = cur.fetchall()

    cur.close()
    con.close()

    return [str(b[0]) for b in birthdays]

def get_real_user_name(user_id):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT 
            CASE 
                WHEN cust_user_name IS NOT NULL AND cust_user_name != '' 
                THEN cust_user_name
                ELSE user_name 
            END AS final_name 
        FROM users 
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()
    cur.close()
    con.close()

    return result[0] if result else None


def check_user_exists(user_id):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()

    cur.close()
    con.close()

    return result is not None


def update_cust_user_name(user_id, cust_user_name):
    if not check_user_exists(user_id):
        return None  # Если пользователя нет, возвращаем None

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("UPDATE users SET cust_user_name = ? WHERE user_id = ?", (cust_user_name, user_id))
    con.commit()

    cur.close()
    con.close()

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

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("UPDATE users SET user_tag = ?, user_name = ? WHERE user_id = ?", (user_name, full_name, user_id))
    con.commit()

    cur.close()
    con.close()

    return True


def update_user_wishlist(user_id, user_wishlist):
    if not check_user_exists(user_id):
        return None

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("UPDATE users SET user_wishlist = ? WHERE user_id = ?", (user_wishlist, user_id))
    con.commit()

    cur.close()
    con.close()


def update_is_approved(user_id, is_approved):
    if not check_user_exists(user_id):
        return None

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("UPDATE users SET is_approved = ? WHERE user_id = ?", (is_approved, user_id))
    con.commit()

    cur.close()
    con.close()


def get_user_info(user_id):

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute(
        "SELECT user_tag, user_name, real_user_name, cust_user_name,"
        "user_day, user_month, user_year, user_wishlist, user_group, user_subgroup, is_approved, schedule_notifications FROM users WHERE user_id = ?",
        (user_id,)
    )
    result = cur.fetchone()

    cur.close()
    con.close()

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
            "schedule_notifications": result[11] if result[11] is not None else 0
        }
    return None

def get_all_user_ids():
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    cur.close()
    con.close()

    return [str(user[0]) for user in users]


def get_user_wishlist(user_tag):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT user_name, user_wishlist FROM users WHERE user_tag = ?", (user_tag,))
    result = cur.fetchone()

    cur.close()
    con.close()

    if not result:
        return "not_found"

    user_name, wishlist = result

    if not wishlist:
        return user_name, "no_wishlist"

    return user_name, wishlist


def set_user_group_subgroup(user_id, user_group, user_subgroup):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("UPDATE users SET user_group = ?, user_subgroup = ? WHERE user_id = ?",
                (user_group, user_subgroup, user_id))

    con.commit()
    cur.close()
    con.close()


def add_user_to_db(user_id, user_tag, user_name):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("INSERT OR IGNORE INTO users (user_id, user_tag, user_name) VALUES (?, ?, ?)",
                (user_id, user_tag, user_name))

    con.commit()
    cur.close()
    con.close()


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
        with sqlite3.connect(BIRTHDAY_DATABASE) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                "SELECT user_id, real_user_name, user_name, is_approved "
                "FROM users WHERE user_group = ?",
                (group_name,)
            )

            for row in cur.fetchall():
                real_name = row['real_user_name'] or row['user_name'] or "Неизвестный"
                students.append({
                    'id': row['user_id'],
                    'name': real_name,
                    'approved': bool(row['is_approved'])
                })
    except sqlite3.Error as e:
        print(f"Ошибка получения студентов: {e}")
    return students


def update_real_user_name(user_id, real_user_name):
    """Обновляет реальное имя пользователя. Возвращает True при успешном обновлении."""
    try:
        with sqlite3.connect(BIRTHDAY_DATABASE) as con:
            cur = con.cursor()
            cur.execute(
                "UPDATE users SET real_user_name = ? WHERE user_id = ?",
                (real_user_name, user_id)
            )
            return cur.rowcount > 0  # True если была изменена хотя бы одна строка
    except sqlite3.Error as e:
        print(f"Ошибка обновления имени для пользователя {user_id}: {e}")
        return False


def toggle_user_approval(user_id: int) -> bool:
    """Переключает статус разрешения поздравлений для пользователя"""
    try:
        with sqlite3.connect(BIRTHDAY_DATABASE) as con:
            cur = con.cursor()

            # Получаем текущее состояние
            cur.execute(
                "SELECT is_approved FROM users WHERE user_id = ?",
                (user_id,)
            )
            current_status = cur.fetchone()[0]

            # Устанавливаем противоположное значение
            new_status = not current_status

            cur.execute(
                "UPDATE users SET is_approved = ? WHERE user_id = ?",
                (new_status, user_id)
            )
            con.commit()
            return new_status
    except sqlite3.Error as e:
        print(f"Ошибка переключения статуса: {e}")
        return False

def get_approval_status(user_id: int) -> bool:
    """Возвращает текущий статус разрешения поздравлений"""
    try:
        with sqlite3.connect(BIRTHDAY_DATABASE) as con:
            cur = con.cursor()
            cur.execute(
                "SELECT is_approved FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cur.fetchone()
            return bool(result[0]) if result else False
    except sqlite3.Error as e:
        print(f"Ошибка получения статуса: {e}")
        return False


def toggle_schedule_notifications(user_id: int) -> bool:
    """Переключает статус рассылки расписания для пользователя"""
    try:
        with sqlite3.connect(BIRTHDAY_DATABASE) as con:
            cur = con.cursor()

            # Получаем текущее состояние
            cur.execute(
                "SELECT schedule_notifications FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cur.fetchone()
            current_status = bool(result[0]) if result and result[0] is not None else False

            # Устанавливаем противоположное значение
            new_status = not current_status

            cur.execute(
                "UPDATE users SET schedule_notifications = ? WHERE user_id = ?",
                (new_status, user_id)
            )
            con.commit()
            return new_status
    except sqlite3.Error as e:
        print(f"Ошибка переключения статуса рассылки расписания: {e}")
        return False


def get_schedule_notifications_status(user_id: int) -> bool:
    """Возвращает текущий статус рассылки расписания"""
    try:
        with sqlite3.connect(BIRTHDAY_DATABASE) as con:
            cur = con.cursor()
            cur.execute(
                "SELECT schedule_notifications FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = cur.fetchone()
            return bool(result[0]) if result and result[0] is not None else False
    except sqlite3.Error as e:
        print(f"Ошибка получения статуса рассылки расписания: {e}")
        return False


def clear_users():
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("DELETE FROM users")

    con.commit()
    cur.close()
    con.close()


def get_id_from_username(username):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT user_id FROM users WHERE user_tag = ?", (username,))
    result = cur.fetchone()

    cur.close()
    con.close()

    if not result:
        return "not_found"

    return result


def check_user_by_username(username: str) -> bool:
    """
    Проверяет, существует ли пользователь с данным username в таблице users.
    :param username: username без @
    :return: True, если пользователь есть в базе, иначе False
    """
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT 1 FROM users WHERE user_tag = ?", (username,))
    result = cur.fetchone()

    cur.close()
    con.close()

    return result is not None
