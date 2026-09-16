from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.contest import get_contest_rules_keyboard

rules_router = Router()

CONTEST_RULES_TEXT = (
    "🎁 <b>Условия розыгрыша Telegram Premium</b>\n\n"
    "Чтобы принять участие и побороться за подписку, выполните базовые условия в период проведения конкурса:\n\n"
    "<b>1.</b> Убедитесь, что у Вас указана учебная группа (во вкладке «Профиль»).\n"
    "<b>2.</b> Проявляйте активность: посмотрите расписание в боте минимум в <b>3 разных дня</b>.\n"
    "<b>3.</b> Приглашайте друзей: у Вас должно быть минимум <b>3 активных друга</b>. Друг считается активным, если он есть у Вас во вкладке «Друзья» и тоже смотрел расписание 3 дня минимум.\n\n"
    "📈 <b>Как повысить свои шансы?</b>\n"
    "Победитель выбирается случайным образом, но <b>каждый</b> добавленный друг увеличивает Вашу вероятность победы! Активные друзья дают максимальный буст, но даже неактивные принесут Вам дополнительные очки.\n\n"
    "<i>Переходите во вкладку «Друзья» из главного меню, добавляйте одногруппников и напоминайте им  расписание!</i> 🚀"
)


@rules_router.callback_query(F.data == "contest_rules")
async def contest_rules_handler(callback: CallbackQuery):

    await callback.message.edit_text(
        text=CONTEST_RULES_TEXT,
        parse_mode="HTML",
        reply_markup=get_contest_rules_keyboard(),
    )

    await callback.answer()