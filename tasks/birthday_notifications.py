# tasks/birthday_notifications

import asyncio
import pytz

from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from datetime import datetime, timedelta

from utils.logger import write_user_log
from utils.database import check_users, get_user_info, check_users_in_7_days
from utils.group_utils import load_groups
from utils.user_utils import is_user_accessible
from utils.database_utils.friends import get_list_friends

from bot import bot

tz_moscow = pytz.timezone("Europe/Moscow")


async def check_birthdays():
    while True:
        now = datetime.now(tz=tz_moscow)

        next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)

        time_to_sleep = (next_run - now).total_seconds()
        msg = f"Следующая проверка дней рождения в {next_run} (через {time_to_sleep} секунд)"
        write_user_log(msg)

        await asyncio.sleep(time_to_sleep)

        # Получаем всех пользователей с ДР сегодня
        birthdays_today = check_users()

        if birthdays_today:
            group_messages = {}  # {chat_id: [messages]}

            groups = await load_groups()

            for UserID in birthdays_today:
                user_info = get_user_info(UserID)

                # Блок отправки в группу
                if user_info["is_approved"]:
                    UserNAME = f"{user_info.get('real_user_name') or user_info.get('user_name')}" \
                               f"{' @' + user_info['user_tag'] if user_info.get('user_tag') else ''}"

                    user_group = user_info.get("user_group")

                    if not user_group or user_group not in groups:
                        continue  # Если группы нет в JSON, пропускаем

                    chat_id = groups[user_group]["chat_id"]

                    user_name = user_info["real_user_name"]
                    if not user_name:
                        user_name = user_info['user_name']

                    # Проверяем, доступен ли пользователь
                    if not await is_user_accessible(UserID):
                        write_user_log(f"Пользователь {UserID} недоступен для поздравления")
                        continue

                    # Создаём инлайн-кнопку для перехода в чат с пользователем
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f"🎉 Поздравить {user_name}", url=f"tg://user?id={UserID}")]
                    ])

                    message = (
                        f"🎉 Дорогой(-ая) {UserNAME}, поздравляем тебя с днём рождения! 🎂\n"
                        "Желаем здоровья, удачи и исполнения всех мечт!\n"
                        "Пусть каждый новый день будет полон позитивных эмоций и улыбок. 🎁"
                    )

                    if chat_id not in group_messages:
                        group_messages[chat_id] = []
                    group_messages[chat_id].append((message, keyboard))

                # Блок отправки друзьям
                user_info = get_user_info(UserID)
                user_name = user_info['user_name']
                friend_ids = get_list_friends(UserID)
                if friend_ids:
                    for friend_id in friend_ids:
                        keyboard_friend = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f"🎉 Поздравить {user_name}", url=f"tg://user?id={UserID}")],
                            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
                        ])
                        name_str = f"{user_name} @{user_info['user_tag']}" if user_info.get('user_tag') else f"{user_name}"
                        msg_friend = (
                            f"🎉 У вашего друга {name_str} сегодня день рождения! 🎂\n"
                            "Обязательно поздравьте его! 🎁"
                        )
                        await bot.send_message(
                            chat_id=friend_id,
                            text=msg_friend,
                            reply_markup=keyboard_friend
                        )
                        write_user_log(f"Сообщение о дне рождения отправлено пользователю {friend_id}")

                # Блок поздравления пользователя в личных сообщениях
                msg_user = (
                    f"🎉 Дорогой(-ая) {user_name}, поздравляю тебя с днём рождения! 🎂\n"
                    "Желаю здоровья, удачи и исполнения всех мечт!\n"
                    "Пусть каждый новый день будет полон позитивных эмоций и улыбок. 🎁"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
                        ])
                await bot.send_message(
                    chat_id=UserID,
                    text=msg_user,
                    reply_markup=keyboard
                )

            # Отправляем сообщения в группы
            for chat_id, messages in group_messages.items():
                for msg, kb in messages:
                    await bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb)
                write_user_log(f"Сообщение о дне рождения отправлено в группу {chat_id}")

        # Проверка дней рождения через неделю
        upcoming_birthdays = check_users_in_7_days()

        if upcoming_birthdays:
            group_messages = {}  # {chat_id: [messages]}

            groups = await load_groups()

            for UserID in upcoming_birthdays:
                user_info = get_user_info(UserID)
                if user_info["is_approved"]:
                    UserNAME = f"{user_info.get('real_user_name') or user_info.get('user_name')}" \
                               f"{' @' + user_info['user_tag'] if user_info.get('user_tag') else ''}"

                    user_group = user_info["user_group"]

                    if not user_group or user_group not in groups:
                        continue  # Пропускаем, если группы нет в JSON

                    UserWISHLIST = user_info["user_wishlist"]
                    if not UserWISHLIST:
                        UserWISHLIST = "Отсутствует"

                    chat_id = groups[user_group]["chat_id"]

                    message = (
                        f"📅 Ровно через неделю {UserNAME} празднует свой день рождения! 🥳\n"
                        f"Самое время готовить подарки! 🎁\n"
                        f"🎈 Вишлист: {UserWISHLIST}"
                    )

                    if chat_id not in group_messages:
                        group_messages[chat_id] = []
                    group_messages[chat_id].append(message)

                # Блок отправки друзьям
                user_info = get_user_info(UserID)
                user_name = user_info['user_name']
                user_wishlist = user_info['user_wishlist'] or "Отсутствует"
                friend_ids = get_list_friends(UserID)
                if friend_ids:
                    for friend_id in friend_ids:
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f"👤 В профиль {user_name}", url=f"tg://user?id={UserID}")],
                            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
                        ])
                        name_str = f"{user_name} @{user_info['user_tag']}" if user_info.get('user_tag') else f"{user_name}"
                        msg_friend = (
                            f"📅 Ровно через неделю {name_str} празднует свой день рождения! 🥳\n"
                            f"Самое время готовить подарки! 🎁\n"
                            f"🎈 Вишлист: {user_wishlist}"
                        )
                        await bot.send_message(
                            chat_id=friend_id,
                            text=msg_friend,
                            reply_markup=keyboard
                        )
                        write_user_log(f"Сообщение о будущем дне рождения отправлено пользователю {friend_id}")

            # Отправляем сообщения в группы
            for chat_id, messages in group_messages.items():
                for msg in messages:
                    await bot.send_message(chat_id=chat_id, text=msg)
                write_user_log(f"Сообщение о будущих именинниках отправлено в группу {chat_id}")