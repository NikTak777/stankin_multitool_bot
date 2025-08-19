from bot import bot, dp
import asyncio
import logging

from handlers import start, info, birthdate, group_registration, admin_panel, edit_profile
from utils.logger import write_user_log
from utils import set_user_birthdate

# Отключение ненужных логов от aiogram
# logging.getLogger("aiogram.event").setLevel(logging.WARNING)

# Подключаем роутеры
dp.include_router(start.router)
dp.include_router(info.router)
dp.include_router(birthdate.router)
dp.include_router(set_user_birthdate.router)
dp.include_router(group_registration.router)
dp.include_router(admin_panel.router)
dp.include_router(edit_profile.router)

async def main():
    """Запуск бота"""
    write_user_log("Бот запущен!")  # Логирует запуск
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())