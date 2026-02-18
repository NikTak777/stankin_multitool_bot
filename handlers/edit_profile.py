from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from utils.logger import write_user_log
from utils.user_utils import get_user_name
from utils.database import toggle_schedule_notifications, get_user_info, get_schedule_notifications_status
from keyboards.edit_profile import get_edit_profile_inline_keyboard

from decorators.sync_username import sync_username

router = Router()


@router.callback_query(lambda c: c.data == "edit_profile_menu")
@sync_username
async def edit_profile_menu(callback: types.CallbackQuery, state: FSMContext):

    await state.clear()  # Сброс состояния

    user_id = callback.from_user.id
    user_name = await get_user_name(callback)

    write_user_log(f"Пользователь {callback.from_user.full_name} ({user_id}) перешёл в меню редактирования профиля")

    inline_keyboard = get_edit_profile_inline_keyboard(user_id)

    await callback.message.edit_text(
        f"Привет, {user_name}!\n\nВыбери, что хочешь изменить в профиле:",
        reply_markup=inline_keyboard
    )

    await callback.answer() # Убрать эффект загрузки


@router.callback_query(lambda c: c.data == "toggle_schedule_notifications")
@sync_username
async def toggle_schedule_notifications_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик переключения настройки рассылки расписания"""
    user_id = callback.from_user.id
    user_name = await get_user_name(callback)
    
    # Получаем текущий статус и информацию о пользователе
    current_status = get_schedule_notifications_status(user_id)
    user_info = get_user_info(user_id)
    
    # Если пользователь пытается включить рассылку, проверяем наличие группы
    if not current_status:  # Текущий статус выключен, значит пытается включить
        if not user_info or not user_info.get("user_group"):
            await callback.answer(
                "❌ Невозможно включить рассылку расписания без указания группы. Пожалуйста, сначала укажите номер группы в настройках.",
                show_alert=True
            )
            return
    
    # Переключаем настройку
    new_status = toggle_schedule_notifications(user_id)
    
    status_text = "включена" if new_status else "выключена"
    await callback.answer(f"Рассылка расписания {status_text}", show_alert=True)
    
    write_user_log(f"Пользователь {callback.from_user.full_name} ({user_id}) {'включил' if new_status else 'выключил'} рассылку расписания")
    
    # Обновляем клавиатуру с новым статусом
    inline_keyboard = get_edit_profile_inline_keyboard(user_id)
    
    try:
        await callback.message.edit_text(
            f"Привет, {user_name}!\n\nВыбери, что хочешь изменить в профиле:",
            reply_markup=inline_keyboard
        )
    except Exception as e:
        write_user_log(f"Ошибка при обновлении сообщения: {e}")
