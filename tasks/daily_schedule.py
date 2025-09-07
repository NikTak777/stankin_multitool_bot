# tasks/daily_schedule
import asyncio
from datetime import datetime, timedelta
import pytz

from utils.logger import write_user_log  # Функция логирования
from utils.schedule_utils import load_groups, is_group_file_exists
from services.schedule_service import format_schedule, load_schedule

from bot import bot  # Импорт бота для отправки сообщений

tz_moscow = pytz.timezone("Europe/Moscow")

# антидубль только "в этот час" для конкретной даты
# ключ: (group_name, 'YYYY-MM-DD', hour)
_sent_this_hour: set[tuple[str, str, int]] = set()


def _now_msk() -> datetime:
    return datetime.now(tz=tz_moscow)


def _is_within_night_window(hour: int) -> bool:
    # 18:00–23:59 или 00:00–05:59
    return (hour >= 18) or (hour < 6)


def _compute_target_date(now: datetime) -> datetime.date:
    # >= 18:00 -> на завтра, иначе (0–5:59) -> на сегодня
    return (now + timedelta(days=1)).date() if now.hour >= 18 else now.date()


async def send_daily_schedule():
    """
    Проверяем раз в час. Если час совпадает с send_hour группы и сейчас :00 минут —
    отправляем расписание. Антидубль действует только на этот (group, date, hour).
    """
    write_user_log("⏳ Планировщик расписаний запущен (окно 20:00–08:00).")

    while True:
        try:
            now = _now_msk()

            if not _is_within_night_window(now.hour):
                next_20 = now.replace(hour=18, minute=0, second=0, microsecond=0)
                if now >= next_20:
                    next_20 += timedelta(days=1)
                await asyncio.sleep((next_20 - now).total_seconds())
                continue

            if now.minute != 0:
                next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                await asyncio.sleep((next_hour - now).total_seconds())
                continue

            groups = await load_groups()
            for group_name, group_data in groups.items():
                chat_id = group_data.get("chat_id")
                send_hour = group_data.get("send_hour", 20)

                if not isinstance(send_hour, int) or not (0 <= send_hour < 24):
                    write_user_log(
                        f"⚠️ {group_name}: некорректный send_hour={send_hour}, использую 20."
                    )
                    send_hour = 20

                # у группы час в допустимом окне?
                if not _is_within_night_window(send_hour):
                    continue

                # срабатываем строго в запрошенный час и в минуту :00
                if now.hour != send_hour:
                    continue

                target_date = _compute_target_date(now)
                key = (group_name, target_date.isoformat(), now.hour)

                # антидубль ТОЛЬКО на этот час
                if key in _sent_this_hour:
                    continue

                if not is_group_file_exists(group_name):
                    write_user_log(f"⚠️ {group_name}: нет файла расписания.")
                    _sent_this_hour.add(key)
                    continue

                try:
                    data = load_schedule(f"{group_name}.json")
                    schedule_text = format_schedule(
                        data, target_date.day, target_date.month, group_name, subgroup="Common"
                    )
                    await bot.send_message(chat_id, schedule_text, parse_mode="HTML")
                    write_user_log(
                        f"✅ Расписание ({target_date.isoformat()}) отправлено в {group_name} (час={now.hour:02d})"
                     )
                except Exception as e:
                    write_user_log(f"❌ Ошибка отправки в {group_name} (chat_id={chat_id}): {e}")
                finally:
                    _sent_this_hour.add(key)

            # очистим старые ключи, чтобы set не разрастался
            # (храним только текущую дату)
            today_iso = _now_msk().date().isoformat()
            _sent_this_hour_copy = set()
            for g, d, h in _sent_this_hour:
                if d == today_iso:
                    _sent_this_hour_copy.add((g, d, h))
            _sent_this_hour.clear()
            _sent_this_hour.update(_sent_this_hour_copy)

            # спим ровно до следующего часа
            now2 = _now_msk()
            next_hour = (now2 + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            await asyncio.sleep((next_hour - now2).total_seconds())

        except Exception as e:
            write_user_log(f"❌ Ошибка планировщика расписаний: {e}")
            await asyncio.sleep(60)
