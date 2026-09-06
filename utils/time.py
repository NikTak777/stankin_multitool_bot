from datetime import datetime
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

def get_now_time() -> datetime:
    """Возвращает текущее московское время."""
    return datetime.now(tz=MOSCOW_TZ)