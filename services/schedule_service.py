from datetime import datetime, timedelta
from utils.schedule_utils import is_group_file_exists
from utils.database import get_user_info

import json
from datetime import datetime
from typing import List, Dict, Any
import pytz


def get_schedule_for_date(user_id: int, day: int, month: int) -> str:
    """Возвращает расписание на указанную дату"""
    user_info = get_user_info(user_id)
    group, subgroup = user_info["user_group"], user_info["user_subgroup"]

    if not is_group_file_exists(group):
        return None

    data = load_schedule(group + ".json")
    return format_schedule(data, day, month, group, subgroup=subgroup)

def format_date(day, month, year=None):
    if year is None:
        return f"{day:02}.{month:02}"
    return f"{day:02}.{month:02}.{year}"


def load_schedule(filename: str) -> List[Dict[str, Any]]:
    """Загружает расписание из JSON файла."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_date_range(date_range: str) -> tuple[datetime, datetime]:
    """Парсит диапазон дат формата YYYY.MM.DD-YYYY.MM.DD"""
    start_str, end_str = date_range.split('-')
    start_date = datetime.strptime(start_str, "%Y.%m.%d")
    end_date = datetime.strptime(end_str, "%Y.%m.%d")
    return start_date, end_date


def is_subject_on_date(subject: Dict[str, Any], target_date: datetime) -> bool:
    """Проверяет, проходит ли предмет в указанную дату."""
    for date_info in subject["dates"]:
        freq = date_info["frequency"]
        date_str = date_info["date"]

        if freq == "once":
            # Проверяем точное совпадение даты
            lesson_date = datetime.strptime(date_str, "%Y.%m.%d")
            if lesson_date.date() == target_date.date():
                return True

        elif freq == "throughout":
            # Проверяем, попадает ли дата в диапазон
            start_date, end_date = parse_date_range(date_str)
            if start_date.date() <= target_date.date() <= end_date.date():
                # Исправляем проверку на занятия через неделю
                delta_days = (target_date - start_date).days
                if delta_days % 14 == 0:  # Каждые две недели
                    return True

        elif freq == "every":
            # Проверяем, что день недели совпадает
            start_date, end_date = parse_date_range(date_str)
            if start_date.date() <= target_date.date() <= end_date.date():
                delta_days = (target_date - start_date).days
                if delta_days % 7 == 0:  # Каждую неделю
                    return True

    return False


def format_schedule(schedule: List[Dict[str, Any]], day: int, month: int, group: str, subgroup: str = "Common") -> str:
    """Форматирует расписание занятий в красивое сообщение с учетом подгруппы или всех занятий."""
    try:
        tz_moscow = pytz.timezone("Europe/Moscow")  # Часовой пояс Москвы
        current_year = datetime.now(tz=tz_moscow).year
        target_date = datetime(current_year, month, day)
    except ValueError:
        return "incorrect date"

    # Словарь перевода типов занятий
    subject_types = {
        "Lecture": "Лекция",
        "Seminar": "Семинар",
        "Laboratory": "Лабораторная"
    }

    # Если subgroup == "Common", показываем все занятия (и A, и B, и Common)
    if subgroup == "Common":
        subjects_on_date = [subj for subj in schedule if is_subject_on_date(subj, target_date)]
    else:
        subjects_on_date = [
            subj for subj in schedule if is_subject_on_date(subj, target_date) and
            (subj["subgroup"] == subgroup or subj["subgroup"] == "Common")
        ]

    formatted_date = format_date(day, month)

    # Преобразуем подгруппы A → А, B → Б
    subgroup_translated = {"A": "А", "B": "Б"}.get(subgroup, subgroup)

    if not subjects_on_date:
        if subgroup == "Common":
            return f"📅 На {formatted_date} у группы {group} занятий нет."
        else:
            return f"📅 На {formatted_date} у подгруппы {subgroup_translated} занятий нет."

    # Сортируем по времени начала
    subjects_on_date.sort(key=lambda x: datetime.strptime(x["time"]["start"], "%H:%M"))

    formatted_subjects = []
    for subj in subjects_on_date:
        title = subj["title"]
        lecturer = subj["lecturer"] or "Не указан"
        subject_type = subject_types.get(subj["type"], subj["type"])  # Перевод типа занятия
        classroom = subj["classroom"] or "Не указана"
        time_start = subj["time"]["start"]
        time_end = subj["time"]["end"]

        # Переводим подгруппы A → А, B → Б
        subj_subgroup_translated = {"A": "А", "B": "Б"}.get(subj["subgroup"], subj["subgroup"])
        subgroup_info = f", подгруппа {subj_subgroup_translated}" if subj["subgroup"] != "Common" else ""

        formatted_subjects.append(
            f"⏰ <b>{time_start} — {time_end}</b>{subgroup_info}\n"
            f" {title} ({subject_type})\n"
            f" {lecturer}, ауд. {classroom}\n"
        )

    if subgroup == "Common":
        return f"📅 Расписание группы {group} на {formatted_date}:\n\n" + "\n".join(formatted_subjects)
    else:
        return f"📅 Расписание подгруппы {subgroup_translated} на {formatted_date}:\n\n" + "\n".join(formatted_subjects)