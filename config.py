# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Настройки бота, загружаемые из переменных окружения"""

    TOKEN: str = Field(..., description="Telegram Bot Token")

    BIRTHDAY_DATABASE: str = Field(default="database/birthdate_list.db", description="Path to birthday database")

    ADMIN_ID: int = Field(..., description="Telegram Admin User ID")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Игнорировать дополнительные переменные из .env
    )


# Создаем экземпляр настроек
try:
    settings = Settings()
except Exception as e:
    # Если .env файл не найден или есть ошибки
    raise RuntimeError(
        f"Ошибка загрузки конфигурации из .env файла: {e}\n"
        "Убедитесь, что файл .env существует и содержит все необходимые переменные:\n"
        "TOKEN=your_bot_token\n"
        "ADMIN_ID=your_admin_id\n"
        "BIRTHDAY_DATABASE=database/birthdate_list.db"
    ) from e

TOKEN = settings.TOKEN
BIRTHDAY_DATABASE = settings.BIRTHDAY_DATABASE
ADMIN_ID = settings.ADMIN_ID
