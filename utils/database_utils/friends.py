import sqlite3
import pytz
from datetime import datetime, timedelta

from config import BIRTHDAY_DATABASE

tz_moscow = pytz.timezone("Europe/Moscow")


def add_friend_request(sender_id: int, receiver_id: int) -> int:
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Добавляем запись о запросе
    cur.execute("""
        INSERT INTO friend_requests (sender_id, receiver_id, status)
        VALUES (?, ?, 'pending')
    """, (sender_id, receiver_id))

    con.commit()

    # Получаем ID последнего добавленного запроса (ID запроса)
    request_id = cur.lastrowid

    cur.close()
    con.close()

    # Возвращаем ID запроса
    return request_id


def delete_friend_request(request_id: int) -> None:
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Добавляем запись о запросе
    cur.execute("""
        DELETE FROM friend_requests
        WHERE id = ?
    """, (request_id,))

    con.commit()
    cur.close()
    con.close()


def update_friend_request_status(request_id: int, status: str):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        UPDATE friend_requests
        SET status = ?
        WHERE id = ?
    """, (status, request_id))

    con.commit()
    cur.close()
    con.close()


def check_existing_request(sender_id: int, receiver_id: int) -> bool:
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT 1 FROM friend_requests
        WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
    """, (sender_id, receiver_id))

    exists = cur.fetchone() is not None
    cur.close()
    con.close()
    return exists


def check_existing_friend(user_id: int, friend_id: int):
    friends = get_list_friends(user_id)
    for friend in friends:
        if str(friend_id) == friend:
            return True
    return False


def add_friend_to_user(user_id: int, friend_id: int):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Получаем текущий список друзей
    cur.execute("SELECT friends FROM users WHERE user_id = ?", (user_id,))
    friends_str = cur.fetchone()[0]
    friends = friends_str.split(",") if friends_str else []

    # Добавляем нового друга, если его нет в списке
    if str(friend_id) not in friends:
        friends.append(str(friend_id))

    # Обновляем список друзей
    cur.execute("""
        UPDATE users
        SET friends = ?
        WHERE user_id = ?
    """, (",".join(friends), user_id))

    con.commit()
    cur.close()
    con.close()


def get_friend_id_from_request_id(request_id: int) -> int:
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Выполняем запрос для получения receiver_id по request_id
    cur.execute("SELECT sender_id FROM friend_requests WHERE id = ?", (request_id,))
    result = cur.fetchone()  # Получаем первую строку

    if result:  # Если результат найден, возвращаем ID друга
        friend_id = result[0]
        cur.close()
        con.close()
        return friend_id

    # Если результат не найден, выбрасываем исключение с объяснением
    cur.close()
    con.close()
    raise ValueError(f"Запрос с ID {request_id} не найден в базе данных.")


def get_list_friends(user_id: int) -> list[int]:
    """
    Функция для получения списка id друзей пользователя
    :param user_id
    :return friend_ids
    """
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("SELECT friends FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    friends_str = result[0] if result else ""
    friend_ids = friends_str.split(",") if friends_str else []

    cur.close()
    con.close()
    return friend_ids


def get_friends_info(user_id: int) -> list[tuple[int, str]]:
    """
    Вернёт список кортежей (friend_id, user_name) в том же порядке,
    в каком friend_id хранятся у пользователя.
    """

    friend_ids = get_list_friends(user_id)
    if not friend_ids:
        return []

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    placeholders = ",".join("?" for _ in friend_ids)
    cur.execute(
        f"SELECT user_id, user_name FROM users WHERE user_id IN ({placeholders})",
        friend_ids
    )

    rows = cur.fetchall()
    cur.close()
    con.close()

    # Собираем dict[int, str], где ключ — user_id, значение — имя
    name_by_id: dict[int, str] = {
        int(uid): str(uname) if uname else "Неизвестный"
        for uid, uname in rows
    }

    # Собираем пары (id, имя) в исходном порядке
    pairs: list[tuple[int, str]] = [
        (int(fid), name_by_id.get(int(fid), "Неизвестный"))
        for fid in friend_ids
    ]
    return pairs


def get_today_birthdays(user_id: int):
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Получаем список айди друзей
    friend_ids = get_list_friends(user_id)

    today = datetime.today()

    today_birthdays = []

    for friend_id in friend_ids:
        cur.execute("SELECT user_name, user_tag, user_day, user_month, user_wishlist FROM users WHERE user_id = ?", (friend_id,))
        row = cur.fetchone()
        if row:
            user_name, user_tag, user_day, user_month, user_wishlist = row

            if not user_day or not user_month:
                continue

            if not user_wishlist: user_wishlist = "Отсутствует"

            user_day = int(user_day)
            user_month = int(user_month)

            birthday_today = safe_date(today.year, user_month, user_day)
            days_until_birthday = (today - birthday_today).days

            if days_until_birthday == 0:
                today_birthdays.append({
                    'user_name': user_name,
                    'user_tag': user_tag,
                    'user_day': user_day,
                    'user_month': user_month,
                    'user_wishlist': user_wishlist
                })

    cur.close()
    con.close()

    return today_birthdays


def get_upcoming_birthdays(user_id: int, days: int = 7) -> list[dict]:
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    # Получаем список айди друзей
    friend_ids = get_list_friends(user_id)

    today = datetime.today()
    upcoming = []

    # Сначала проходим по друзьям и собираем тех, у кого ДР в ближайшие days дней
    for friend_id in friend_ids:
        cur.execute("SELECT user_name, user_tag, user_day, user_month, user_wishlist FROM users WHERE user_id = ?", (friend_id,))
        row = cur.fetchone()
        if row:
            user_name, user_tag, user_day, user_month, user_wishlist = row

            if not user_day or not user_month:
                continue

            if not user_wishlist: user_wishlist = "Отсутствует"

            user_day = int(user_day)
            user_month = int(user_month)
            # Делаем объект даты для ближайшего ДР
            birthday_this_year = safe_date(today.year, user_month, user_day)
            days_until_birthday = (birthday_this_year - today).days

            # Если ДР уже прошёл в этом году, считаем на следующий год
            if days_until_birthday < 0:
                birthday_next_year = safe_date(today.year + 1, user_month, user_day)
                days_until_birthday = (birthday_next_year - today).days

            if 0 <= days_until_birthday <= days:
                upcoming.append({
                    'user_name': user_name,
                    'user_tag': user_tag,
                    'user_day': user_day,
                    'user_month': user_month,
                    'user_wishlist': user_wishlist,
                    'days_until': days_until_birthday
                })

    # Если в ближайшие days дней никого нет, добавляем одного самого ближайшего
    if not upcoming:
        closest = None
        min_days = 365
        for friend_id in friend_ids:
            cur.execute("SELECT user_name, user_tag, user_day, user_month, user_wishlist FROM users WHERE user_id = ?", (friend_id,))
            row = cur.fetchone()
            if row:
                user_name, user_tag, user_day, user_month, user_wishlist = row

                if not user_day or not user_month:
                    continue

                if not user_wishlist: user_wishlist = "Отсутствует"

                user_day = int(user_day)
                user_month = int(user_month)

                birthday_this_year = safe_date(today.year, user_month, user_day)
                days_until_birthday = (birthday_this_year - today).days
                if days_until_birthday < 0:
                    birthday_next_year = safe_date(today.year + 1, user_month, user_day)
                    days_until_birthday = (birthday_next_year - today).days

                if days_until_birthday < min_days and days_until_birthday < 364:
                    min_days = days_until_birthday
                    closest = {
                        'user_name': user_name,
                        'user_tag': user_tag,
                        'user_day': user_day,
                        'user_month': user_month,
                        'user_wishlist': user_wishlist,
                        'days_until': days_until_birthday
                    }
        if closest:
            upcoming.append(closest)

    # Закрываем соединение
    cur.close()
    con.close()

    # Сортируем по ближайшему дню рождения
    upcoming.sort(key=lambda x: x['days_until'])

    # Убираем вспомогательное поле 'days_until' перед возвратом
    for u in upcoming:
        u.pop('days_until')

    return upcoming


def delete_friend(user_id: int, friend_id: int) -> None:
    """
    Удаляет friend_id из списка друзей user_id
    """

    friend_id = str(friend_id)
    ids = get_list_friends(user_id)
    new_ids = [fid for fid in ids if fid != friend_id]

    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()
    cur.execute(
        "UPDATE users SET friends = ? WHERE user_id = ?",
        (",".join(new_ids), user_id)
    )
    con.commit()
    cur.close()
    con.close()


def safe_date(year: int, month: int, day: int) -> datetime:
    """Создаёт дату, безопасно обрабатывая 29 февраля."""
    try:
        return datetime(year=year, month=month, day=day)
    except ValueError:
        if month == 2 and day == 29:
            return datetime(year=year, month=2, day=28)
        raise


# Функции для работы с предложениями вишлистов

def add_wishlist_suggestion(sender_id: int, receiver_id: int, wishlist_text: str) -> int:
    """Добавляет предложение вишлиста и возвращает ID предложения."""
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO wishlist_suggestions (sender_id, receiver_id, wishlist_text, status)
        VALUES (?, ?, ?, 'pending')
    """, (sender_id, receiver_id, wishlist_text))

    con.commit()
    suggestion_id = cur.lastrowid
    cur.close()
    con.close()

    return suggestion_id


def get_wishlist_suggestion(suggestion_id: int) -> dict | None:
    """Получает информацию о предложении вишлиста по ID."""
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        SELECT sender_id, receiver_id, wishlist_text, status
        FROM wishlist_suggestions
        WHERE id = ?
    """, (suggestion_id,))

    result = cur.fetchone()
    cur.close()
    con.close()

    if result:
        return {
            "sender_id": result[0],
            "receiver_id": result[1],
            "wishlist_text": result[2],
            "status": result[3]
        }
    return None


def update_wishlist_suggestion_status(suggestion_id: int, status: str):
    """Обновляет статус предложения вишлиста."""
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        UPDATE wishlist_suggestions
        SET status = ?
        WHERE id = ?
    """, (status, suggestion_id))

    con.commit()
    cur.close()
    con.close()


def delete_wishlist_suggestion(suggestion_id: int):
    """Удаляет предложение вишлиста."""
    con = sqlite3.connect(BIRTHDAY_DATABASE)
    cur = con.cursor()

    cur.execute("""
        DELETE FROM wishlist_suggestions
        WHERE id = ?
    """, (suggestion_id,))

    con.commit()
    cur.close()
    con.close()