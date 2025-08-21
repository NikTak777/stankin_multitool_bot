import os

import json
import aiofiles

from utils.logger import write_user_log

def is_group_file_exists(group_name: str) -> bool:
    """
    Синхронно проверяет, существует ли файл с расписанием группы.

    :param group_name: Название группы (например, "ИДБ-23-10")
    :return: True, если файл существует, иначе False
    """
    file_path = f"{group_name}.json"
    return os.path.exists(file_path)

async def load_groups():
    """Асинхронная загрузка данных из JSON с защитой от ошибок."""
    file_path = "groups.json"

    if not os.path.exists(file_path):
        msg = f"⚠️ Файл {file_path} не найден. Создаётся новый."
        await write_user_log(msg)
        await save_groups({})  # Создаем пустой JSON
        return {}

    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()
            groups = json.loads(content) if content else {}  # Если файл пуст, возвращаем {}
            if not isinstance(groups, dict):
                msg = f"⚠️ Ошибка: Ожидался объект JSON, но получено другое. Восстанавливается файл"
                await write_user_log(msg)
                await save_groups({})
                return {}
            return groups
    except json.JSONDecodeError:
        msg = f"❌ Ошибка: Некорректный JSON в {file_path}. Восстанавливается файл"
        await write_user_log(msg)
        await save_groups({})
        return {}
    except Exception as e:
        msg = f"❌ Ошибка при открытии {file_path}: {e}"
        await write_user_log(msg)
        return {}


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


def get_group_name_by_id(group_id: int, groups_dict: dict) -> str | None:
    for group_name, group_data in groups_dict.items():
        if group_data["chat_id"] == group_id:
            return group_name
    return None