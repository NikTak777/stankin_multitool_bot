import json
import os
import aiofiles

from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from bot import bot

from utils.logger import write_user_log

GROUPS_FILE = "groups.json"
TEMP_FILE = "groups_temp.json"


async def load_groups() -> dict:
    try:
        async with aiofiles.open(GROUPS_FILE, "r", encoding="utf-8") as f:
            data = await f.read()
            return json.loads(data) if data else {}
    except FileNotFoundError:
        return {}


async def save_groups(groups: dict):
    """Асинхронно сохраняет данные в JSON с безопасной записью."""
    try:
        async with aiofiles.open(TEMP_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(groups, indent=4, ensure_ascii=False))
        os.replace(TEMP_FILE, GROUPS_FILE)
    except Exception as e:
        await write_user_log(f"❌ Ошибка при сохранении группы {groups}: {e}")


def get_group_name_by_id(group_id: int, groups_dict: dict) -> str | None:
    for group_name, group_data in groups_dict.items():
        if group_data["chat_id"] == group_id:
            return group_name
    return None


def is_valid_group_name(name: str) -> bool:
    # Валидация: XXX-00-00
    import re
    return bool(re.match(r"^[А-ЯA-Z]{2,}-\d{2}-\d{2}$", name))

async def is_group_file_exists(group_name: str) -> bool:
    """
    Асинхронно проверяет, существует ли файл с расписанием группы.

    :param group_name: Название группы (например, "ИДБ-23-10")
    :return: True, если файл существует, иначе False
    """
    file_path = f"{group_name}.json"
    return os.path.exists(file_path)

async def is_bot_admin(chat_id: int) -> bool:
    """Проверяет, является ли сам бот админом группы."""
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        return isinstance(bot_member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception as e:
        print(f"⚠️ Ошибка при проверке прав бота в группе {chat_id}: {e}")
        return False


def is_group_registered(chat_id: int, groups: dict) -> bool:
    """Проверяет, зарегистрирована ли группа по chat_id."""
    if not isinstance(groups, dict):  # если groups повреждён
        return False
    return any(group_data.get("chat_id") == chat_id for group_data in groups.values())

async def save_groups(groups: dict):
    """Асинхронно сохраняет данные в JSON с безопасной записью."""
    temp_file = "groups_temp.json"
    file_path = "groups.json"

    try:
        async with aiofiles.open(temp_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(groups, indent=4, ensure_ascii=False))

        os.replace(temp_file, file_path)  # Безопасное обновление файла
    except Exception as e:
        msg = f"❌ Ошибка при сохранении группы {groups}: {e}"
        await write_user_log(msg)
