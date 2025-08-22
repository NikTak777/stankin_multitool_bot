# tasks/daily_schedule
import asyncio
from datetime import datetime, timedelta
import pytz

from utils.logger import write_user_log  # Функция логирования
from utils.schedule_utils import load_groups, is_group_file_exists
from services.schedule_service import format_schedule, load_schedule

from bot import bot  # Импорт бота для отправки сообщений

tz_moscow = pytz.timezone("Europe/Moscow")

async def send_daily_schedule():
    while True:
        now = datetime.now(tz=tz_moscow)

        next_run = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)

        time_to_sleep = (next_run - now).total_seconds()

        msg = f"⏳ Следующая отправка расписания групп в {next_run} (через {time_to_sleep} секунд)"
        write_user_log(msg)

        await asyncio.sleep(time_to_sleep)

        now = datetime.now(tz=tz_moscow)
        tomorrow = now + timedelta(days=1)
        day = tomorrow.day
        month = tomorrow.month

        groups = await load_groups()

        for group_name, group_data in groups.items():
            chat_id = group_data["chat_id"]

            if is_group_file_exists(group_name):
                data = load_schedule(group_name + ".json")
                schedule_text = format_schedule(data, day, month, group_name, subgroup="Common")
                try:
                    await bot.send_message(chat_id, schedule_text, parse_mode="HTML")
                    msg = f"✅ Сообщение отправлено в {group_name} (Chat ID: {chat_id})"
                except Exception as e:
                    msg = f"❌ Ошибка при отправке в {group_name}: {e}"
                write_user_log(msg)
            else:
                msg = f"Группа {group_name} не получила расписания, так как его нет в системе"
                write_user_log(msg)