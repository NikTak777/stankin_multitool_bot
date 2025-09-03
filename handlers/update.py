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
        "🎓 <b>Поздравляем с началом нового учебного года!</b> 🎉\n\n"
        "Бот снова работает и готов помогать вам весь семестр. 🚀\n\n"
        "📅 <b>Расписание</b>\n"
        "Теперь бот рассылает расписание по всем группам бакалавриата (актуальные и проверенные).\n\n"
        "🎂 <b>Поздравления</b>\n"
        "Бот продолжает радовать студентов поздравлениями с днём рождения. 🥳\n\n"
        "👥 <b>Регистрация группы</b>\n"
        "Чтобы всё заработало, старосте нужно зарегистрировать группу командой <b>/init</b>.\n\n"
        "✨ <b>Новый интерфейс</b>\n"
        "Меню стало удобнее и интуитивно понятнее.\n\n"
        "🏆 Успехов в новом учебном году!"
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