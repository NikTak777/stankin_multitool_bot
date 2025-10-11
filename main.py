# main.py
from bot import bot, dp
import asyncio

from handlers import (start_menu, info, birthdate, group_registration, group_panel, edit_profile,
                      other_profile, user_wishlist, user_group, schedule, help, user_nickname,
                      update, admin_panel)
from handlers.friends import friends_menu, friends_request, friends_edit_menu, delete_friend, friend_profile

from handlers.schedule_modules import other_group

from utils.logger import write_user_log
from utils import set_user_birthdate
from utils.database_utils.init_database import init_database

from tasks.daily_schedule import send_daily_schedule
from tasks.birthday_notifications import check_birthdays

from middlewares.user_activity import ActivityMiddleware

# Отключение ненужных логов от aiogram
# logging.getLogger("aiogram.event").setLevel(logging.WARNING)

# Подключаем роутеры
dp.update.middleware(ActivityMiddleware())
dp.include_router(start_menu.router)
dp.include_router(info.router)
dp.include_router(birthdate.router)
dp.include_router(set_user_birthdate.router)
dp.include_router(group_registration.router)
dp.include_router(group_panel.router)
dp.include_router(edit_profile.router)
dp.include_router(other_profile.router)
dp.include_router(user_wishlist.router)
dp.include_router(user_group.router)
dp.include_router(schedule.router)
dp.include_router(help.router)
dp.include_router(user_nickname.router)
dp.include_router(update.router)
dp.include_router(admin_panel.router)
dp.include_router(friends_request.router)
dp.include_router(friends_menu.router)
dp.include_router(friends_edit_menu.router)
dp.include_router(delete_friend.router)
dp.include_router(friend_profile.router)
dp.include_router(other_group.router)


async def main():
    """Запуск бота"""
    write_user_log("Бот запущен!")  # Логирует запуск

    init_database()

    # запускаем рассылку параллельно с ботом
    asyncio.create_task(send_daily_schedule())
    asyncio.create_task(check_birthdays())

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())