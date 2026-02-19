# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Настройки бота, загружаемые из переменных окружения"""

    TOKEN: str = Field(..., description="Telegram Bot Token")
    ADMIN_ID: int = Field(..., description="Telegram Admin User ID")
    
    # PostgreSQL настройки
    DB_HOST: str = Field(default="localhost", description="PostgreSQL host")
    DB_PORT: int = Field(default=5432, description="PostgreSQL port")
    DB_NAME: str = Field(default="users", description="Database name")
    DB_USER: str = Field(default="postgres", description="Database user")
    DB_PASSWORD: str = Field(..., description="Database password")
    
    # Для обратной совместимости при миграции (можно удалить позже)
    BIRTHDAY_DATABASE: str = Field(default="database/birthdate_list.db", description="Legacy SQLite path (for migration)")
    
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
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "DB_NAME=users\n"
        "DB_USER=postgres\n"
        "DB_PASSWORD=your_password"
    ) from e

TOKEN = settings.TOKEN
ADMIN_ID = settings.ADMIN_ID

# PostgreSQL настройки
DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_NAME = settings.DB_NAME
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD

# Для обратной совместимости
BIRTHDAY_DATABASE = settings.BIRTHDAY_DATABASE
