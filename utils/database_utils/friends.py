import pytz
from datetime import datetime, timedelta

from utils.db_connection import get_db_connection

tz_moscow = pytz.timezone("Europe/Moscow")


def add_friend_request(sender_id: int, receiver_id: int) -> int:
    with get_db_connection() as con:
        cur = con.cursor()

        # Добавляем запись о запросе и получаем ID
        cur.execute("""
            INSERT INTO friend_requests (sender_id, receiver_id, status)
            VALUES (%s, %s, 'pending')
            RETURNING id
        """, (sender_id, receiver_id))

        # Получаем ID последнего добавленного запроса
        request_id = cur.fetchone()[0]

        # Возвращаем ID запроса
        return request_id


def delete_friend_request(request_id: int) -> None:
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            DELETE FROM friend_requests
            WHERE id = %s
        """, (request_id,))


def update_friend_request_status(request_id: int, status: str):
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            UPDATE friend_requests
            SET status = %s
            WHERE id = %s
        """, (status, request_id))


def check_existing_request(sender_id: int, receiver_id: int) -> bool:
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT 1 FROM friend_requests
            WHERE sender_id = %s AND receiver_id = %s AND status = 'pending'
        """, (sender_id, receiver_id))

        exists = cur.fetchone() is not None
        return exists


def check_existing_friend(user_id: int, friend_id: int):
    friends = get_list_friends(user_id)
    for friend in friends:
        if str(friend_id) == friend:
            return True
    return False


def add_friend_to_user(user_id: int, friend_id: int):
    with get_db_connection() as con:
        cur = con.cursor()

        # Получаем текущий список друзей
        cur.execute("SELECT friends FROM users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        friends_str = result[0] if result and result[0] else ""
        friends = friends_str.split(",") if friends_str else []

        # Добавляем нового друга, если его нет в списке
        if str(friend_id) not in friends:
            friends.append(str(friend_id))

        # Обновляем список друзей
        cur.execute("""
            UPDATE users
            SET friends = %s
            WHERE user_id = %s
        """, (",".join(friends), user_id))


def get_friend_id_from_request_id(request_id: int) -> int:
    with get_db_connection() as con:
        cur = con.cursor()

        # Выполняем запрос для получения sender_id по request_id
        cur.execute("SELECT sender_id FROM friend_requests WHERE id = %s", (request_id,))
        result = cur.fetchone()  # Получаем первую строку

        if result:  # Если результат найден, возвращаем ID друга
            friend_id = result[0]
            return friend_id

        # Если результат не найден, выбрасываем исключение с объяснением
        raise ValueError(f"Запрос с ID {request_id} не найден в базе данных.")


def get_list_friends(user_id: int) -> list[int]:
    """
    Функция для получения списка id друзей пользователя
    :param user_id
    :return friend_ids
    """
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("SELECT friends FROM users WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        friends_str = result[0] if result and result[0] else ""
        friend_ids = friends_str.split(",") if friends_str else []

        return friend_ids


def get_friends_info(user_id: int) -> list[tuple[int, str]]:
    """
    Вернёт список кортежей (friend_id, user_name) в том же порядке,
    в каком friend_id хранятся у пользователя.
    """

    friend_ids = get_list_friends(user_id)
    if not friend_ids:
        return []

    with get_db_connection() as con:
        cur = con.cursor()

        # PostgreSQL использует %s для всех параметров, но для IN нужно использовать ANY
        placeholders = ",".join("%s" for _ in friend_ids)
        cur.execute(
            f"SELECT user_id, user_name FROM users WHERE user_id IN ({placeholders})",
            friend_ids
        )

        rows = cur.fetchall()

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
    with get_db_connection() as con:
        cur = con.cursor()

        # Получаем список айди друзей
        friend_ids = get_list_friends(user_id)

        today = datetime.today()

        today_birthdays = []

        for friend_id in friend_ids:
            cur.execute("SELECT user_name, user_tag, user_day, user_month, user_wishlist FROM users WHERE user_id = %s", (friend_id,))
            row = cur.fetchone()
            if row:
                user_name, user_tag, user_day, user_month, user_wishlist = row

                if not user_day or not user_month:
                    continue

                if not user_wishlist:
                    user_wishlist = "Отсутствует"

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

        return today_birthdays


def get_upcoming_birthdays(user_id: int, days: int = 7) -> list[dict]:
    with get_db_connection() as con:
        cur = con.cursor()

        # Получаем список айди друзей
        friend_ids = get_list_friends(user_id)

        today = datetime.today()
        upcoming = []

        # Сначала проходим по друзьям и собираем тех, у кого ДР в ближайшие days дней
        for friend_id in friend_ids:
            cur.execute("SELECT user_name, user_tag, user_day, user_month, user_wishlist FROM users WHERE user_id = %s", (friend_id,))
            row = cur.fetchone()
            if row:
                user_name, user_tag, user_day, user_month, user_wishlist = row

                if not user_day or not user_month:
                    continue

                if not user_wishlist:
                    user_wishlist = "Отсутствует"

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
                cur.execute("SELECT user_name, user_tag, user_day, user_month, user_wishlist FROM users WHERE user_id = %s", (friend_id,))
                row = cur.fetchone()
                if row:
                    user_name, user_tag, user_day, user_month, user_wishlist = row

                    if not user_day or not user_month:
                        continue

                    if not user_wishlist:
                        user_wishlist = "Отсутствует"

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

    with get_db_connection() as con:
        cur = con.cursor()
        cur.execute(
            "UPDATE users SET friends = %s WHERE user_id = %s",
            (",".join(new_ids), user_id)
        )


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
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            INSERT INTO wishlist_suggestions (sender_id, receiver_id, wishlist_text, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING id
        """, (sender_id, receiver_id, wishlist_text))

        suggestion_id = cur.fetchone()[0]
        return suggestion_id


def get_wishlist_suggestion(suggestion_id: int) -> dict | None:
    """Получает информацию о предложении вишлиста по ID."""
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            SELECT sender_id, receiver_id, wishlist_text, status
            FROM wishlist_suggestions
            WHERE id = %s
        """, (suggestion_id,))

        result = cur.fetchone()

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
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            UPDATE wishlist_suggestions
            SET status = %s
            WHERE id = %s
        """, (status, suggestion_id))


def delete_wishlist_suggestion(suggestion_id: int):
    """Удаляет предложение вишлиста."""
    with get_db_connection() as con:
        cur = con.cursor()

        cur.execute("""
            DELETE FROM wishlist_suggestions
            WHERE id = %s
        """, (suggestion_id,))
