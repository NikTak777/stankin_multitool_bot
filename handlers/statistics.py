# handlers/statistics.py
from aiogram import types, Router, F
from aiogram.types import CallbackQuery

from utils.logger import write_user_log
from utils.user_utils import get_user_name
from utils.database_utils.database_statistic import (
    get_user_rank_by_activity, 
    get_user_rank_by_days, 
    get_user_statistics
)
from keyboards.back_to_menu import get_back_inline_keyboard

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db

router = Router()


@router.callback_query(F.data == "statistics")
@sync_username
@ensure_user_in_db
async def show_statistics(callback: CallbackQuery):
    """Показывает статистику пользователя"""
    user_id = callback.from_user.id
    user_name = await get_user_name(callback.from_user)
    
    write_user_log(f"Пользователь {callback.from_user.full_name} ({user_id}) запросил статистику")
    
    # Получаем статистику
    stats = get_user_statistics(user_id)
    rank_activity = get_user_rank_by_activity(user_id)
    rank_days = get_user_rank_by_days(user_id)
    
    # Формируем сообщение
    rank_activity_text = f"#{rank_activity}" if rank_activity > 0 else "Нет данных"
    rank_days_text = f"#{rank_days}" if rank_days > 0 else "Нет данных"
    
    message_text = (
        f"Привет, {user_name}!\n\n"
        f"📊 Ваша статистика:\n\n"
        f"🎯 Место в топе по количеству действий: {rank_activity_text} ({stats['total_actions']} действий)\n"
        f"📅 Место в топе по количеству дней: {rank_days_text} ({stats['days_count']} дней)\n"
        f"📈 Среднее количество действий в день: {stats['avg_actions_per_day']}\n"
        f"⏱ Длительность использования: {stats['days_since_first']} дней"
    )
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_back_inline_keyboard("info")
    )
    await callback.answer()

