from aiogram import types, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot
from utils.logger import write_user_log
from utils.database import get_all_user_ids

from decorators.admin_only import admin_only

router = Router()


@router.message(Command("update"))
@admin_only
async def select_update(message: types.Message):

    update_message = (
        "🎁 <b>Осенний розыгрыш Telegram Premium!</b> 🚀\n\n"
        "Учебный год только начался, а <b>Stankin Multitool</b> уже раздаёт подарки! Запускаем масштабный конкурс для самых активных студентов. Забирай подписку Telegram Premium, просто пользуясь ботом! 😎\n\n"

        "👇 <b>Что нужно для участия?</b>\n"
        "<b>1.</b> Укажи свою учебную группу в Профиле.\n"
        "<b>2.</b> Посмотри расписание в боте минимум в <b>3 разных дня</b>.\n"
        "<b>3.</b> Добавь минимум <b>3 друзей</b> во вкладке «Друзья», которые тоже зайдут посмотреть расписание 3 раза.\n\n"

        "📈 <b>Лайфхак: как повысить шансы?</b>\n"
        "Победитель выберется случайно, но твои шансы зависят от тебя! <b>Каждый</b> добавленный друг увеличивает вероятность победы. Активные друзья дают максимальный буст (3 очка), но даже неактивные принесут пользу (1 очко).\n\n"

        "⏳ <b>Сроки:</b> с 18 по 28 сентября.\n\n"
        "🏆 <i>Добавляй одногруппников, следи за своим местом в топе прямо в боте и забирай Premium! Удачи!</i>"
    )

    old_update_message = (
        "<b>Привет! Спишь?</b> 🌙\n\n"
        "А вот бот <b>Stankin Multitool</b> больше не спит! Специально к 1 сентября мы перенесли расписание <b>всех групп бакалавриата</b>. 🎓\n\n"
        "Теперь вы можете узнавать свои пары круглосуточно: хоть днём, хоть ночью — расписание всегда под рукой. 🦉\n\n"
        "🔜 <i>Также в скором времени будет добавлено расписание для магистратуры и специалитета!</i> 🚀\n\n"
        "🛠 <b>Поддержка</b>\n"
        "Если вы заметите какие-либо ошибки или у вас возникнут вопросы, пожалуйста, "
        "напишите в поддержку: @NikTak_YT. Мы всегда готовы помочь! 🧑‍💻\n\n"
        "🏆 С Днём знаний, удачи в новом семестре и приятного пользования ботом!"
    )

    user_ids = get_all_user_ids()

    successful = 0
    failed = 0

    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=update_message,
                parse_mode="HTML",
                reply_markup=get_inline_keyboard()
            )
            successful += 1
        except Exception as e:
            msg = f"Не удалось отправить сообщение пользователю с ID {user_id}: {e}"
            write_user_log(msg)
            failed += 1

    # Подтверждение для администратора
    await message.answer(
        f"📢 Рассылка завершена.\n✅ Успешно отправлено: {successful}\n❌ Ошибки: {failed}"
    )


def get_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ваш прогресс", callback_data="contest")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
    ])