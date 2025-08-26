from bot import bot, dp
import asyncio
import logging

from handlers import (start_menu, info, birthdate, group_registration, admin_panel, edit_profile,
                      friend_wishlist, user_wishlist, user_group, schedule, help, user_nickname)

from utils.logger import write_user_log
from utils import set_user_birthdate

from tasks.daily_schedule import send_daily_schedule
from tasks.birthday_notifications import check_birthdays

# Отключение ненужных логов от aiogram
# logging.getLogger("aiogram.event").setLevel(logging.WARNING)

# Подключаем роутеры
dp.include_router(start_menu.router)
dp.include_router(info.router)
dp.include_router(birthdate.router)
dp.include_router(set_user_birthdate.router)
dp.include_router(group_registration.router)
dp.include_router(admin_panel.router)
dp.include_router(edit_profile.router)
dp.include_router(friend_wishlist.router)
dp.include_router(user_wishlist.router)
dp.include_router(user_group.router)
dp.include_router(schedule.router)
dp.include_router(help.router)
dp.include_router(user_nickname.router)


async def main():
    """Запуск бота"""
    write_user_log("Бот запущен!")  # Логирует запуск

    # запускаем рассылку параллельно с ботом
    asyncio.create_task(send_daily_schedule())
    asyncio.create_task(check_birthdays())

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())