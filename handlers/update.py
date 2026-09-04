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
        "<b>Привет! Спишь?</b> 🌙\n\n"
        "А вот бот <b>Stankin Multitool</b> больше не спит! Специально к 1 сентября мы перенесли расписание <b>всех групп бакалавриата</b>. 🎓\n\n"
        "Теперь вы можете узнавать свои пары круглосуточно: хоть днём, хоть ночью — расписание всегда под рукой. 🦉\n\n"
        "🔜 <i>Также в скором времени будет добавлено расписание для магистратуры и специалитета!</i> 🚀\n\n"
        "🛠 <b>Поддержка</b>\n"
        "Если вы заметите какие-либо ошибки или у вас возникнут вопросы, пожалуйста, "
        "напишите в поддержку: @NikTak_YT. Мы всегда готовы помочь! 🧑‍💻\n\n"
        "🏆 С Днём знаний, удачи в новом семестре и приятного пользования ботом!"
    )

    old_update_message = (
        "🎓 <b>Бот обновился!</b> 🚀\n\n"
        "Теперь у нас ещё больше возможностей и полезных функций для студентов. 💫\n\n"

        "🔔 <b>Уведомления о парах</b>\n"
        "Бот научился присылать уведомления о предстоящих парах прямо в личные сообщения. "
        "Включить это можно в настройках профиля /info ⏰\n\n"
        
        "📚 <b>Расписание для всех</b>\n"
        "Отличная новость: практически все группы бакалавриата доступны для просмотра расписания! "
        "Находите свою группу и будьте в курсе всех пар. ✅\n\n"

        "📈 <b>Статистика</b>\n"
        "Теперь вы можете смотреть свою статистику, "
        "а также статистику друзей, чтобы соревноваться в активном использовании бота! 📊\n\n"

        "🎁 <b>Вишлист для друзей</b>\n"
        "Теперь вы можете предлагать вишлист своим друзьям. "
        "Это можно сделать из списка друзей /friends 💝\n\n"

        "🛠️ <b>Поддержка</b>\n"
        "Если вы заметите какие-либо ошибки или у вас возникнут вопросы, пожалуйста, "
        "напишите в поддержку: @NikTak_YT. Мы всегда готовы помочь! 🧑‍💻\n\n"

        "🏆 Удачи в этом семестре и приятного пользования ботом!"
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
        [InlineKeyboardButton(text="Перейти в меню ➡️", callback_data="start")]
    ])