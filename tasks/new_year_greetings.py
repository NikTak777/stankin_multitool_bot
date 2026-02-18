# tasks/new_year_greetings.py

import asyncio
import pytz

from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from datetime import datetime, timedelta

from utils.logger import write_user_log
from utils.database import get_all_user_ids, get_user_info
from utils.group_utils import load_groups
from utils.user_utils import is_user_accessible
from utils.database_utils.task_management import get_task_status

from bot import bot

tz_moscow = pytz.timezone("Europe/Moscow")


async def check_new_year():
    while True:
        # Проверяем, включен ли таск
        if not get_task_status("new_year_greetings"):
            # Если таск выключен, проверяем раз в день
            now = datetime.now(tz=tz_moscow)
            next_check = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            time_to_sleep = (next_check - now).total_seconds()
            await asyncio.sleep(time_to_sleep)
            continue
        
        now = datetime.now(tz=tz_moscow)

        # Проверяем, наступил ли Новый год (1 января)
        # Если сегодня 1 января, отправляем поздравления
        if now.month == 1 and now.day == 1:
            # Отправляем в 9:00 утра
            next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # Если еще не 9:00, ждем до 9:00
            if now < next_run:
                time_to_sleep = (next_run - now).total_seconds()
                msg = f"Следующая отправка новогодних поздравлений в {next_run} (через {time_to_sleep} секунд)"
                write_user_log(msg)
                await asyncio.sleep(time_to_sleep)
            
            # Если уже прошло 9:00, отправляем сразу (на случай, если бот только что запустился)
            # Но только если прошло не более 2 часов после 9:00 (чтобы не отправлять поздно вечером)
            if now.hour >= 9 and now.hour < 11:
                write_user_log("Отправка новогодних поздравлений...")
            elif now.hour >= 11:
                # Если уже поздно (после 11:00), пропускаем и ждем до следующего года
                next_year = now.replace(year=now.year + 1, month=1, day=1, hour=9, minute=0, second=0, microsecond=0)
                time_to_sleep = (next_year - now).total_seconds()
                msg = f"Время отправки новогодних поздравлений прошло. Следующая отправка в {next_year} (через {time_to_sleep} секунд)"
                write_user_log(msg)
                await asyncio.sleep(time_to_sleep)
                continue

            # Отправляем поздравления всем пользователям
            all_user_ids = get_all_user_ids()
            groups = await load_groups()
            
            # Отправка личных сообщений всем пользователям
            for user_id_str in all_user_ids:
                try:
                    user_id = int(user_id_str)
                    user_info = get_user_info(user_id)
                    
                    if not user_info:
                        continue
                    
                    user_name = user_info.get('real_user_name') or user_info.get('user_name', 'студент')
                    
                    # Проверяем, доступен ли пользователь
                    if not await is_user_accessible(user_id):
                        write_user_log(f"Пользователь {user_id} недоступен для новогоднего поздравления")
                        continue
                    
                    # Личное сообщение в единственном числе
                    personal_message = (
                        f"🎄 Дорогой(-ая) {user_name}! 🎄\n\n"
                        f"🎉 Поздравляю тебя с Новым годом! 🎉\n"
                        f"Пусть этот год принесет тебе только радость, вдохновение и множество ярких моментов! ✨\n\n"
                        f"📚 Хочу пожелать тебе удачной сдачи сессии, которая еще впереди! Твоя упорная работа и старания обязательно принесут плоды! 🌟\n\n"
                        f"💫 Желаю, чтобы в новом году сбылись все твои мечты, а каждый день дарил новые возможности для роста и развития. Пусть рядом будут верные друзья, а каждый день будет полон ярких событий! 🎊\n\n"
                        f"🎁 Счастливого Нового года и удачи в будущем! 🎈"
                    )
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
                    ])
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=personal_message,
                        reply_markup=keyboard
                    )
                    write_user_log(f"Новогоднее поздравление отправлено пользователю {user_id}")
                
                except Exception as e:
                    write_user_log(f"Ошибка при отправке новогоднего поздравления пользователю {user_id_str}: {e}")
                    continue
            
            # Отправляем сообщения во все группы из groups.json
            for group_name, group_data in groups.items():
                try:
                    chat_id = group_data.get("chat_id")
                    if not chat_id:
                        write_user_log(f"⚠️ У группы {group_name} отсутствует chat_id")
                        continue
                    
                    # Сообщение для группы во множественном числе
                    group_message = (
                        f"🎄 Дорогие студенты группы {group_name}! 🎄\n\n"
                        f"🎉 Поздравляем вас с Новым годом! 🎉\n"
                        f"Пусть этот год принесет вам только радость, вдохновение и множество ярких моментов! ✨\n\n"
                        f"📚 Хотим пожелать вам удачной сдачи сессии, которая еще впереди! Ваша упорная работа и старания обязательно принесут плоды! 🌟\n\n"
                        f"💫 Желаем, чтобы в новом году сбылись все ваши мечты, а каждый день дарил новые возможности для роста и развития. Пусть рядом будут верные друзья, а каждый день будет полон ярких событий! 🎊\n\n"
                        f"🎁 Счастливого Нового года и удачи в будущем! 🎈"
                    )
                    
                    await bot.send_message(
                        chat_id=chat_id,
                        text=group_message
                    )
                    write_user_log(f"Новогоднее поздравление отправлено в группу {group_name} (chat_id: {chat_id})")
                
                except Exception as e:
                    write_user_log(f"Ошибка при отправке новогоднего поздравления в группу {group_name} (chat_id: {chat_id}): {e}")
                    continue
            
            write_user_log("Новогодние поздравления успешно отправлены!")
            
            # Ждем до следующего года (1 января следующего года в 9:00)
            next_year = now.replace(year=now.year + 1, month=1, day=1, hour=9, minute=0, second=0, microsecond=0)
            time_to_sleep = (next_year - now).total_seconds()
            msg = f"Следующая отправка новогодних поздравлений в {next_year} (через {time_to_sleep} секунд)"
            write_user_log(msg)
            await asyncio.sleep(time_to_sleep)
        else:
            # Если не 1 января, вычисляем время до следующего 1 января в 9:00
            next_new_year = now.replace(year=now.year, month=1, day=1, hour=9, minute=0, second=0, microsecond=0)
            
            # Если 1 января этого года уже прошло, берем следующий год
            if now > next_new_year:
                next_new_year = next_new_year.replace(year=now.year + 1)
            
            time_to_sleep = (next_new_year - now).total_seconds()
            msg = f"Следующая отправка новогодних поздравлений в {next_new_year} (через {time_to_sleep} секунд)"
            write_user_log(msg)
            await asyncio.sleep(time_to_sleep)

