import logging
from datetime import datetime
import pytz
import os

# Часовой пояс Москвы
tz_moscow = pytz.timezone("Europe/Moscow")

# Создаём папку для логов, если её нет
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Конфигурируем логирование
log_file = os.path.join(LOG_DIR, "bot.log")

logging.basicConfig(
    level=logging.INFO,  # Можно менять на DEBUG, WARNING, ERROR
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ],
)

# Функция логирования
def write_user_log(message: str, level: str = "info"):
    """Логирует действия пользователей и работу бота."""
    # timestamp = datetime.now(tz=tz_moscow).strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{message}"

    # Выбор уровня логирования
    if level == "info":
        logging.info(log_message)
    elif level == "warning":
        logging.warning(log_message)
    elif level == "error":
        logging.error(log_message)
    elif level == "critical":
        logging.critical(log_message)
    else:
        logging.debug(log_message)
