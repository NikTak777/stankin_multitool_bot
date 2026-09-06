from datetime import datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

def get_now_time() -> datetime:
    """Возвращает текущее московское время."""
    return datetime.now(tz=MOSCOW_TZ)

def format_str_to_datetime(str_time: str) -> datetime:
    """Возвращает переведённую дату из строки формата DD-MM-YYYY."""
    return datetime.strptime(str_time, "%d-%m-%Y")