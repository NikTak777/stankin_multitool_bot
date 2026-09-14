from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramForbiddenError

from bot import bot
from decorators.admin_only import admin_only
from decorators.sync_username import sync_username

from utils.user_utils import get_user_name
from utils.database import get_user_info
from utils.logger import write_user_log

from services.contest import start_raffle, get_all_contest_stats

from keyboards.contest import get_admin_contest_menu_keyboard
from keyboards.back_to_menu import get_back_inline_keyboard

raffle_router = Router()


@raffle_router.message(Command("contest"))
@sync_username
@admin_only
async def admin_contest_menu_command(message: Message):
    user = message.from_user
    user_name = await get_user_name(user)
    await message.answer(
        text=(
            f"Привет, {user_name}!\n\n"
            f"{get_all_contest_stats()}"
        ),
        reply_markup=get_admin_contest_menu_keyboard()
    )
    write_user_log(f"Админ {user.full_name} ({user.user_id}) @{user.username} ввёл команду /contest")


@raffle_router.callback_query(F.data == "contest-panel")
@sync_username
@admin_only
async def admin_contest_menu_callback_query(callback: CallbackQuery):
    user = callback.from_user
    user_name = await get_user_name(user)
    await callback.message.edit_text(
        text=(
            f"Привет, {user_name}!\n\n"
            f"{get_all_contest_stats()}"
        ),
        reply_markup=get_admin_contest_menu_keyboard()
    )
    await callback.answer()
    write_user_log(f"Админ {user.full_name} ({user.user_id}) @{user.username} открыл панель администрирования розыгрышем")


@raffle_router.callback_query(F.data == "start-raffle")
@sync_username
@admin_only
async def start_contest_raffle_handler(callback: CallbackQuery):
    user = callback.from_user
    winner_id = start_raffle()
    winner_info = get_user_info(winner_id)
    winner_fullname, winner_username = winner_info["user_name"], winner_info["user_tag"]
    await callback.message.edit_text(
        text=(
            f"Победителем стал: {winner_fullname} @{winner_username}\n\n"
            f"{get_all_contest_stats()}"
        ),
        reply_markup=get_back_inline_keyboard()
    )
    await callback.answer()
    write_user_log(f"Админ {user.full_name} ({user.user_id}) @{user.username} запустил розыгрыш. Победителем стал пользователь {winner_fullname} ({winner_id}) @{winner_username}")

    try:
        await bot.send_message(
            chat_id=winner_id,
            text=(
                f"Привет, {winner_fullname}!\n\n🎉 Поздравляем, Вы стали победителем "
                f"розыгрыша на Telegram Premium! В ближайшее время с Вами свяжется "
                f"наш админ @NikTak_YT для обсуждения процесса получения подписки."
            )
        )
        write_user_log(f"Сообщение о победе в розыгрыше доставлено пользователю {winner_fullname} ({winner_id}) @{winner_username}")

    except TelegramForbiddenError:
        write_user_log(f"Не удалось доставить уведомление пользователю "
                       f"{winner_fullname} ({winner_id}): бот заблокирован")
    except Exception as e:
        write_user_log(f"Не удалось доставить уведомление пользователю "
                       f"{winner_fullname} ({winner_id}): {e}")
