"""
Скрипт для миграции данных из SQLite в PostgreSQL
Запускать один раз после настройки PostgreSQL
"""
import sqlite3
from utils.db_connection import get_db_connection
from utils.logger import write_user_log
from config import BIRTHDAY_DATABASE


def migrate_data():
    """Переносит данные из SQLite в PostgreSQL"""
    
    # Проверяем существование SQLite файла
    try:
        sqlite_conn = sqlite3.connect(BIRTHDAY_DATABASE)
        sqlite_cur = sqlite_conn.cursor()
        write_user_log(f"Подключено к SQLite: {BIRTHDAY_DATABASE}")
    except Exception as e:
        write_user_log(f"Ошибка подключения к SQLite: {e}")
        return False
    
    try:
        with get_db_connection() as pg_conn:
            pg_cur = pg_conn.cursor()
            
            # Миграция таблицы users
            write_user_log("Начинаю миграцию таблицы users...")
            sqlite_cur.execute("SELECT * FROM users")
            users = sqlite_cur.fetchall()
            
            # Получаем названия колонок из SQLite
            sqlite_cur.execute("PRAGMA table_info(users)")
            columns_info = sqlite_cur.fetchall()
            column_names = [col[1] for col in columns_info]
            
            migrated_count = 0
            for user_row in users:
                # Создаем словарь из данных пользователя
                user_dict = dict(zip(column_names, user_row))
                
                # Преобразуем boolean значения (SQLite хранит 0/1, PostgreSQL - True/False)
                is_approved = bool(user_dict.get('is_approved', False)) if user_dict.get('is_approved') is not None else False
                schedule_notifications = bool(user_dict.get('schedule_notifications', False)) if user_dict.get('schedule_notifications') is not None else False
                
                try:
                    pg_cur.execute("""
                        INSERT INTO users (
                            user_id, user_tag, user_name, real_user_name, cust_user_name,
                            user_day, user_month, user_year, user_wishlist,
                            user_group, user_subgroup, is_approved, created_at,
                            friends, schedule_notifications
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s
                        ) ON CONFLICT (user_id) DO NOTHING
                    """, (
                        user_dict.get('user_id'),
                        user_dict.get('user_tag'),
                        user_dict.get('user_name'),
                        user_dict.get('real_user_name'),
                        user_dict.get('cust_user_name'),
                        user_dict.get('user_day'),
                        user_dict.get('user_month'),
                        user_dict.get('user_year'),
                        user_dict.get('user_wishlist'),
                        user_dict.get('user_group'),
                        user_dict.get('user_subgroup'),
                        is_approved,
                        user_dict.get('created_at'),
                        user_dict.get('friends'),
                        schedule_notifications
                    ))
                    migrated_count += 1
                except Exception as e:
                    write_user_log(f"Ошибка при миграции пользователя {user_dict.get('user_id')}: {e}")
            
            write_user_log(f"Мигрировано пользователей: {migrated_count} из {len(users)}")
            
            # Миграция таблицы user_activity
            write_user_log("Начинаю миграцию таблицы user_activity...")
            sqlite_cur.execute("SELECT * FROM user_activity")
            activities = sqlite_cur.fetchall()
            
            activity_count = 0
            for activity in activities:
                try:
                    pg_cur.execute("""
                        INSERT INTO user_activity (id, user_id, event, ts)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, activity)
                    activity_count += 1
                except Exception as e:
                    write_user_log(f"Ошибка при миграции активности: {e}")
            
            write_user_log(f"Мигрировано записей активности: {activity_count} из {len(activities)}")
            
            # Миграция таблицы friend_requests
            write_user_log("Начинаю миграцию таблицы friend_requests...")
            sqlite_cur.execute("SELECT * FROM friend_requests")
            requests = sqlite_cur.fetchall()
            
            request_count = 0
            for request in requests:
                try:
                    pg_cur.execute("""
                        INSERT INTO friend_requests (id, sender_id, receiver_id, status, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, request)
                    request_count += 1
                except Exception as e:
                    write_user_log(f"Ошибка при миграции заявки в друзья: {e}")
            
            write_user_log(f"Мигрировано заявок в друзья: {request_count} из {len(requests)}")
            
            # Миграция таблицы wishlist_suggestions
            write_user_log("Начинаю миграцию таблицы wishlist_suggestions...")
            sqlite_cur.execute("SELECT * FROM wishlist_suggestions")
            suggestions = sqlite_cur.fetchall()
            
            suggestion_count = 0
            for suggestion in suggestions:
                try:
                    pg_cur.execute("""
                        INSERT INTO wishlist_suggestions (id, sender_id, receiver_id, wishlist_text, status, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, suggestion)
                    suggestion_count += 1
                except Exception as e:
                    write_user_log(f"Ошибка при миграции предложения вишлиста: {e}")
            
            write_user_log(f"Мигрировано предложений вишлиста: {suggestion_count} из {len(suggestions)}")
            
            # Миграция таблицы task_settings
            write_user_log("Начинаю миграцию таблицы task_settings...")
            sqlite_cur.execute("SELECT * FROM task_settings")
            tasks = sqlite_cur.fetchall()
            
            task_count = 0
            for task in tasks:
                try:
                    # Преобразуем boolean
                    enabled = bool(task[1]) if task[1] is not None else True
                    pg_cur.execute("""
                        INSERT INTO task_settings (task_name, enabled, updated_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (task_name) DO NOTHING
                    """, (task[0], enabled, task[2]))
                    task_count += 1
                except Exception as e:
                    write_user_log(f"Ошибка при миграции настройки задачи: {e}")
            
            write_user_log(f"Мигрировано настроек задач: {task_count} из {len(tasks)}")
            
            write_user_log("Миграция данных завершена успешно!")
            return True
            
    except Exception as e:
        write_user_log(f"Ошибка при миграции: {e}")
        return False
    finally:
        sqlite_cur.close()
        sqlite_conn.close()


if __name__ == "__main__":
    print("Начинаю миграцию данных из SQLite в PostgreSQL...")
    print("Убедитесь, что PostgreSQL настроен и база данных 'users' создана.")
    input("Нажмите Enter для продолжения...")
    
    if migrate_data():
        print("Миграция завершена успешно!")
    else:
        print("Миграция завершена с ошибками. Проверьте логи.")

