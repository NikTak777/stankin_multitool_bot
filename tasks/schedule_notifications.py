# tasks/schedule_notifications.py

import asyncio
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from utils.logger import write_user_log
from utils.database import get_all_user_ids, get_user_info
from utils.schedule_utils import is_group_file_exists
from utils.user_utils import is_user_accessible
from services.schedule_service import load_schedule, is_subject_on_date
from utils.database_utils.task_management import get_task_status

from bot import bot

tz_moscow = pytz.timezone("Europe/Moscow")

# Словарь для отслеживания отправленных уведомлений
# Ключ: (user_id, date_iso, notification_type, lesson_time)
# notification_type: 'reminder' (за час до первого занятия) или 'ended' (после окончания пары)
_sent_notifications: set[tuple[int, str, str, str]] = set()

def _cleanup_old_notifications(current_date: str):
    """Очищает старые уведомления (не сегодняшние)"""
    global _sent_notifications
    _sent_notifications = {
        (uid, date, ntype, time) 
        for (uid, date, ntype, time) in _sent_notifications 
        if date == current_date
    }

# Словарь перевода типов занятий
SUBJECT_TYPES = {
    "Lecture": "Лекция",
    "Seminar": "Семинар",
    "Laboratory": "Лабораторная"
}


def _now_msk() -> datetime:
    """Возвращает текущее время в часовом поясе Москвы"""
    return datetime.now(tz=tz_moscow)


def _get_user_lessons_for_today(user_id: int, today: datetime) -> List[Dict[str, Any]]:
    """Получает список занятий пользователя на сегодняшний день"""
    user_info = get_user_info(user_id)
    if not user_info:
        return []
    
    user_group = user_info.get("user_group")
    user_subgroup = user_info.get("user_subgroup")
    
    if not user_group or not is_group_file_exists(user_group):
        return []
    
    try:
        schedule_data = load_schedule(f"{user_group}.json")
        lessons_today = []
        
        for subject in schedule_data:
            # Проверяем, проходит ли предмет сегодня
            # Преобразуем aware datetime в naive для совместимости с is_subject_on_date
            today_naive = today.replace(tzinfo=None) if today.tzinfo else today
            if not is_subject_on_date(subject, today_naive):
                continue
            
            # Проверяем подгруппу
            subject_subgroup = subject.get("subgroup", "Common")
            if user_subgroup == "Common":
                # Если у пользователя подгруппа Common, показываем все занятия
                pass
            else:
                # Иначе показываем только свои подгруппы и Common
                if subject_subgroup != "Common" and subject_subgroup != user_subgroup:
                    continue
            
            lessons_today.append(subject)
        
        # Сортируем по времени начала
        lessons_today.sort(key=lambda x: datetime.strptime(x["time"]["start"], "%H:%M"))
        
        return lessons_today
    except Exception as e:
        write_user_log(f"Ошибка при получении расписания для пользователя {user_id}: {e}")
        return []


def _parse_time(time_str: str) -> datetime:
    """Парсит время в формате HH:MM и возвращает datetime с сегодняшней датой"""
    hour, minute = map(int, time_str.split(":"))
    now = _now_msk()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _format_subject_info(subject: Dict[str, Any]) -> str:
    """Форматирует информацию о предмете для сообщения"""
    title = subject["title"]
    lecturer = subject.get("lecturer") or "Не указан"
    subject_type = SUBJECT_TYPES.get(subject["type"], subject["type"])
    classroom = subject.get("classroom") or "Не указана"
    time_start = subject["time"]["start"]
    time_end = subject["time"]["end"]
    
    return f"{title} ({subject_type})", lecturer, classroom, time_start, time_end


async def _send_reminder(user_id: int, first_lesson: Dict[str, Any], today_date: str):
    """Отправляет напоминание за час до первого занятия"""
    try:
        title, lecturer, classroom, time_start, time_end = _format_subject_info(first_lesson)
        
        message = (
            f"⏰ Напоминание о занятии\n\n"
            f"В {time_start} начнётся:\n"
            f"📚 {title}\n"
            f"👨‍🏫 {lecturer}\n"
            f"📍 Аудитория: {classroom}\n"
            f"🕐 {time_start} - {time_end}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
        ])
        
        if not await is_user_accessible(user_id):
            write_user_log(f"Пользователь {user_id} недоступен для уведомления о расписании")
            return False
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=keyboard
        )
        
        write_user_log(f"Напоминание о занятии отправлено пользователю {user_id}")
        return True
    except Exception as e:
        write_user_log(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")
        return False


async def _send_lesson_ended(user_id: int, ended_lesson: Dict[str, Any], 
                             next_lesson: Optional[Dict[str, Any]], today_date: str):
    """Отправляет уведомление об окончании пары"""
    try:
        title, lecturer, classroom, time_start, time_end = _format_subject_info(ended_lesson)
        
        # Определяем род глагола в зависимости от типа занятия
        lesson_type = ended_lesson.get("type", "")
        if lesson_type == "Seminar":
            ended_word = "закончился"
        else:
            ended_word = "закончилась"
        
        if next_lesson:
            next_title, next_lecturer, next_classroom, next_time_start, next_time_end = _format_subject_info(next_lesson)
            
            message = (
                f"✅ {title} {ended_word}\n\n"
                f"В {next_time_start} начнётся:\n"
                f"📚 {next_title}\n"
                f"👨‍🏫 {next_lecturer}\n"
                f"📍 Аудитория: {next_classroom}\n"
                f"🕐 {next_time_start} - {next_time_end}"
            )
        else:
            message = (
                f"✅ {title} {ended_word}\n\n"
                f"На сегодня с занятиями всё. Отдыхайте! 😊"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
        ])
        
        if not await is_user_accessible(user_id):
            write_user_log(f"Пользователь {user_id} недоступен для уведомления о расписании")
            return False
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=keyboard
        )
        
        write_user_log(f"Уведомление об окончании занятия отправлено пользователю {user_id}")
        return True
    except Exception as e:
        write_user_log(f"Ошибка при отправке уведомления об окончании пользователю {user_id}: {e}")
        return False


def _get_next_check_time(now: datetime) -> datetime:
    """Вычисляет следующее время проверки (минута кратна 10: 00, 10, 20, 30, 40, 50)"""
    current_minute = now.minute
    current_second = now.second
    
    # Если текущая минута уже кратна 10 и секунды = 0, следующая проверка через 10 минут
    if current_minute % 10 == 0 and current_second == 0:
        next_minute = current_minute + 10
    else:
        # Вычисляем следующую "круглую" минуту
        next_minute = ((current_minute // 10) + 1) * 10
    
    if next_minute >= 60:
        # Переходим на следующий час
        next_hour = now.hour + 1
        if next_hour >= 24:
            # Переход на следующий день
            next_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
    
    return next_time


async def check_schedule_notifications():
    """Основная функция проверки и отправки уведомлений о расписании"""
    write_user_log("⏳ Планировщик уведомлений о расписании запущен")
    
    while True:
        try:
            # Проверяем, включен ли таск
            if not get_task_status("schedule_notifications"):
                # Если таск выключен, проверяем раз в 10 минут
                await asyncio.sleep(600)
                continue
            
            now = _now_msk()
            today_date = now.date().isoformat()
            
            # Вычисляем следующее время проверки (минута кратна 10)
            next_check_time = _get_next_check_time(now)
            time_until_check = (next_check_time - now).total_seconds()
            
            # Если до следующей проверки больше 0 секунд, ждем
            if time_until_check > 0:
                write_user_log(f"⏰ Следующая проверка в {next_check_time.strftime('%H:%M')} (через {int(time_until_check)} секунд)")
                await asyncio.sleep(time_until_check)
                now = _now_msk()  # Обновляем время после ожидания
                today_date = now.date().isoformat()
            
            # Очищаем старые уведомления (не сегодняшние)
            _cleanup_old_notifications(today_date)
            
            # Получаем всех пользователей
            all_user_ids = get_all_user_ids()
            
            for user_id_str in all_user_ids:
                try:
                    user_id = int(user_id_str)
                    user_info = get_user_info(user_id)
                    
                    if not user_info:
                        continue
                    
                    # Пропускаем пользователей без группы
                    if not user_info.get("user_group"):
                        continue
                    
                    # Пропускаем пользователей с отключенной рассылкой расписания
                    schedule_notifications = user_info.get("schedule_notifications", 0)
                    if not schedule_notifications:
                        continue
                    
                    # Получаем занятия на сегодня
                    lessons_today = _get_user_lessons_for_today(user_id, now)
                    
                    if not lessons_today:
                        continue
                    
                    # Проверяем напоминание за час до первого занятия
                    first_lesson = lessons_today[0]
                    first_lesson_start_str = first_lesson["time"]["start"]
                    first_lesson_start = _parse_time(first_lesson_start_str)
                    
                    # Проверяем, не прошло ли уже время начала первого занятия
                    if now < first_lesson_start:
                        # Вычисляем время за час до начала
                        reminder_time = first_lesson_start - timedelta(hours=1)
                        
                        # Проверяем, находимся ли мы в интервале для отправки напоминания
                        # Отправляем если текущее время >= времени напоминания и <= времени начала занятия
                        if reminder_time <= now < first_lesson_start:
                            reminder_key = (user_id, today_date, 'reminder', first_lesson_start_str)
                            
                            if reminder_key not in _sent_notifications:
                                await _send_reminder(user_id, first_lesson, today_date)
                                _sent_notifications.add(reminder_key)
                    
                    # Проверяем окончание пар
                    for i, lesson in enumerate(lessons_today):
                        lesson_start_str = lesson["time"]["start"]
                        lesson_end_str = lesson["time"]["end"]
                        lesson_end = _parse_time(lesson_end_str)
                        
                        # Проверяем, закончилась ли пара (текущее время >= времени окончания)
                        if now >= lesson_end:
                            # Проверяем, есть ли следующая пара
                            next_lesson = lessons_today[i + 1] if i + 1 < len(lessons_today) else None
                            
                            if next_lesson:
                                # Если есть следующая пара, отправляем уведомление только до её начала
                                next_lesson_start = _parse_time(next_lesson["time"]["start"])
                                if now >= next_lesson_start:
                                    # Если уже началась следующая пара, пропускаем
                                    continue
                            # Если следующей пары нет, отправляем в любое время после окончания последней
                            
                            ended_key = (user_id, today_date, 'ended', lesson_start_str)
                            
                            if ended_key not in _sent_notifications:
                                await _send_lesson_ended(user_id, lesson, next_lesson, today_date)
                                _sent_notifications.add(ended_key)
                
                except Exception as e:
                    write_user_log(f"Ошибка при обработке пользователя {user_id_str}: {e}")
                    continue
        
        except Exception as e:
            write_user_log(f"❌ Ошибка планировщика уведомлений о расписании: {e}")
            await asyncio.sleep(60)  # При ошибке спим минуту перед повтором

