from aiogram import types, Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (ReplyKeyboardRemove, ChatMemberAdministrator,
                           ChatMemberOwner, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardBuilder
from aiogram.filters.state import StateFilter
from aiogram.exceptions import TelegramBadRequest


from utils.group_utils import load_groups, save_groups
from handlers.start_menu import send_start_menu
from utils.user_utils import get_user_name, is_user_group_admin
from utils.logger import write_user_log
from utils.database import get_users_by_group, get_approval_status, toggle_user_approval, update_real_user_name, get_real_user_name
from keyboards.group_panel_keyboards import get_edit_send_time_keyboard, ALLOWED_HOURS, _fmt_hour
from states.group_panel_states import SendTimeState

# Декораторы
from decorators.private_only import private_only
from decorators.sync_username import sync_username
from decorators.ensure_user_in_db import ensure_user_in_db


router = Router()

# Обработчик команды /panel
@router.message(Command("panel"))
@private_only
@ensure_user_in_db
@sync_username
async def cmd_group_panel(message: types.Message):
    await send_admin_panel(
        bot=message.bot,
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        full_name=message.from_user.full_name,
        message=message,          # передаём message
        callback=None             # не из callback
    )


# Обработчик инлайн-кнопки
@router.callback_query(F.data == "panel")
@sync_username
async def handle_panel_callback(callback: types.CallbackQuery):
    await send_admin_panel(
        bot=callback.bot,
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        full_name=callback.from_user.full_name,
        message=callback.message, # передаём callback.message
        callback=callback         # сигнал, что вызвано из callback
    )
    await callback.answer()

async def send_admin_panel(
    bot: Bot,
    user_id: int,
    chat_id: int,
    full_name: str,
    message: types.Message,
    callback: types.CallbackQuery | None
):
    is_admin = await is_user_group_admin(user_id)

    if not is_admin:
        if callback:
            await message.edit_text("❌ У вас нет доступа к панели управления, так как вы не зарегистрированы как староста.")
        else:
            await bot.send_message(chat_id, "❌ У вас нет доступа к панели управления, так как вы не зарегистрированы как староста.")
        return

    groups = await load_groups()

    # Проверяем, является ли пользователь старостой
    user_group = next((group for group, data in groups.items() if data["registered_by"] == user_id), None)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать группу", callback_data="edit_group")],
        [InlineKeyboardButton(text="⏰ Изменить время рассылки", callback_data="edit_send_time")],
        [InlineKeyboardButton(text="🗑 Удалить регистрацию", callback_data="delete_group")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
    ])

    user_name = get_real_user_name(user_id)

    text = (
        f"Привет, {user_name}!\n"
        "Это панель управления вашей группой.\n\n"
        f"📌 Вы являетесь старостой группы {user_group}\n\n"
        "Выберите действие:"
    )

    msg = f"Админ {full_name} ({user_id}) открыл панель управления группой {user_group}"
    write_user_log(msg)

    if callback:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await bot.send_message(chat_id, text, reply_markup=keyboard)

# Определяем состояния
class EditState(StatesGroup):
    browsing = State()
    changing_name = State()


# Функция для создания клавиатуры
def get_edit_keyboard(student_id: int):
    """Создаёт клавиатуру с кнопками управления"""
    builder = InlineKeyboardBuilder()

    # Кнопки перемещения
    builder.row(
        types.InlineKeyboardButton(text="⬆️", callback_data="move_up"),
        types.InlineKeyboardButton(text="⬇️", callback_data="move_down")
    )

    # Кнопка изменения имени
    builder.row(types.InlineKeyboardButton(
        text="✏️ Изменить имя",
        callback_data="change_name"
    ))

    # Кнопка управления поздравлениями
    status = "✅" if get_approval_status(student_id) else "🚫"
    builder.row(types.InlineKeyboardButton(
        text=f"{status} Поздравления",
        callback_data="toggle_approval"
    ))

    # Кнопка возврата
    builder.row(types.InlineKeyboardButton(
        text=" ◀️ Завершить ",
        callback_data="cancel_edit"
    ))

    return builder.as_markup()


# Обработчики
@router.callback_query(lambda c: c.data == "edit_group")
async def handle_edit_group(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    groups = await load_groups()

    user_group = next((g for g, d in groups.items() if d["registered_by"] == user_id), None)
    if not user_group:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    students = get_users_by_group(user_group)
    if not students:
        await callback.answer("❌ В группе нет студентов", show_alert=True)
        msg = f"Панель управления группы админа {callback.from_user.full_name} ({callback.from_user.id}) закрыта. В группе {user_group} нет студентов"
        write_user_log(msg)
        return

    await state.set_state(EditState.browsing)
    await state.update_data(
        current_index=0,
        user_group=user_group,
        message_id=callback.message.message_id
    )

    await update_group_view(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        state=state
    )


async def update_group_view(bot: Bot, chat_id: int, message_id: int, state: FSMContext):
    data = await state.get_data()
    user_group = data['user_group']
    current_index = data['current_index']

    students = get_users_by_group(user_group)
    if not students:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ В группе больше нет студентов"
        )
        await state.clear()
        return

    student_list = "\n".join(
        f"👉 {'✅' if s['approved'] else '🚫'} {s['name']}"
        if i == current_index
        else f"👤 {'✅' if s['approved'] else '🚫'} {s['name']}"
        for i, s in enumerate(students)
    )

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Список студентов:\n\n{student_list}\n\nВыберите действие:",
            reply_markup=get_edit_keyboard(students[current_index]['id'])
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(EditState.browsing, lambda c: c.data in ["move_up", "move_down"])
async def handle_move(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    students = get_users_by_group(data['user_group'])

    new_index = (data['current_index'] + (-1 if callback.data == "move_up" else 1)) % len(students)

    await state.update_data(current_index=new_index)
    await callback.answer()

    await update_group_view(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=data['message_id'],
        state=state
    )


@router.callback_query(EditState.browsing, lambda c: c.data == "change_name")
async def handle_change_name(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    students = get_users_by_group(data['user_group'])

    await state.update_data(
        selected_student_id=students[data['current_index']]['id'],
        original_name=students[data['current_index']]['name']
    )

    msg = (f"Админ {callback.from_user.full_name} ({callback.from_user.id}) группы {data['user_group']} "
           f"начал указывать имя пользователя {students[data['current_index']]['name']} ({students[data['current_index']]['id']})")
    write_user_log(msg)

    await callback.message.answer(f"✏️ Введите новое имя для {students[data['current_index']]['name']}:")
    await state.set_state(EditState.changing_name)


@router.message(EditState.changing_name)
async def handle_new_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_name = message.text.strip()

    if not new_name or new_name == data['original_name']:
        # await message.answer("❌ Имя не может быть пустым или совпадать с предыдущим")
        msg = (f"Админ {message.from_user.full_name} ({message.from_user.id}) группы {data['user_group']} "
               f"не изменил имя пользователя ({data['selected_student_id']})")
        write_user_log(msg)

        # Удаляем старое сообщение со списком
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['message_id']
            )
        except TelegramBadRequest:
            pass

        # Получаем актуальный список студентов
        students = get_users_by_group(data['user_group'])
        current_index = data['current_index']

        # Создаем новое сообщение со списком
        student_list = "\n".join(
            f"👉 {'✅' if s['approved'] else '🚫'} {s['name']}"
            if i == current_index
            else f"👤 {'✅' if s['approved'] else '🚫'} {s['name']}"
            for i, s in enumerate(students)
        )

        # Отправляем новое сообщение
        new_msg = await message.answer(
            f"❌ Имя не может быть пустым или совпадать с предыдущим\n\n"
            f"Список студентов:\n\n{student_list}\n\nВыберите действие:",
            reply_markup=get_edit_keyboard(students[current_index]['id'])
        )

        # Обновляем состояние с новым message_id
        await state.update_data(
            message_id=new_msg.message_id,
            current_index=data['current_index']
        )
        await state.set_state(EditState.browsing)
        return

    if update_real_user_name(data['selected_student_id'], new_name):

        msg = (f"Админ {message.from_user.full_name} ({message.from_user.id}) группы {data['user_group']} "
               f"изменил имя пользователя {new_name} ({data['selected_student_id']})")
        write_user_log(msg)

        # Удаляем старое сообщение со списком
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=data['message_id']
            )
        except TelegramBadRequest:
            pass

        # Получаем актуальный список студентов
        students = get_users_by_group(data['user_group'])
        current_index = data['current_index']

        # Создаем новое сообщение со списком
        student_list = "\n".join(
            f"👉 {'✅' if s['approved'] else '🚫'} {s['name']}"
            if i == current_index
            else f"👤 {'✅' if s['approved'] else '🚫'} {s['name']}"
            for i, s in enumerate(students)
        )

        # Отправляем новое сообщение
        new_msg = await message.answer(
            f"✅ Имя успешно обновлено!\n\n"
            f"Список студентов:\n\n{student_list}\n\nВыберите действие:",
            reply_markup=get_edit_keyboard(students[current_index]['id'])
        )

        # Обновляем состояние с новым message_id
        await state.update_data(
            message_id=new_msg.message_id,
            current_index=data['current_index']
        )
        await state.set_state(EditState.browsing)
    else:
        await message.answer("❌ Ошибка при обновлении имени")


@router.callback_query(EditState.browsing, lambda c: c.data == "toggle_approval")
async def handle_toggle_approval(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    students = get_users_by_group(data['user_group'])
    current_student = students[data['current_index']]

    # Получаем новый статус
    new_status = toggle_user_approval(current_student['id'])

    if new_status is not None:
        status_text = "разрешены" if new_status else "запрещены"
        await callback.answer(f"Поздравления для {current_student['name']} {status_text}", show_alert=True)

        msg = (f"Админ {callback.from_user.full_name} ({callback.from_user.id}) изменил "
               f"статус поздравлений пользователя {current_student['name']} ({current_student['id']}) на '{status_text}'")
        write_user_log(msg)

        # Обновляем отображение
        await update_group_view(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=data['message_id'],
            state=state
        )
    else:
        await callback.answer("❌ Ошибка изменения статуса", show_alert=True)


@router.callback_query(EditState.browsing, lambda c: c.data == "cancel_edit")
async def handle_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "✅ Редактирование группы успешно завершено",
            reply_markup=None
        )
        groups = await load_groups()
        user_group = next((group for group, data in groups.items() if data["registered_by"] == callback.from_user.id), None)
        msg = f"Админ {callback.from_user.full_name} ({callback.from_user.id}) закрыл панель управления группой {user_group}"
        write_user_log(msg)
    except TelegramBadRequest:
        pass

    # Отправляем стартовое меню отдельным сообщением
    await send_start_menu(callback, new_message=True)
    await callback.answer()


class DeleteGroupState(StatesGroup):
    waiting_for_confirmation = State()


@router.callback_query(lambda c: c.data == "delete_group")
async def delete_group(callback: types.CallbackQuery, state: FSMContext):
    """Запрос на подтверждение удаления группы"""
    user_id = callback.from_user.id
    groups_data = await load_groups()

    user_group = next((group for group, data in groups_data.items() if data["registered_by"] == user_id), None)

    if not user_group:
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return

    await state.update_data(group_to_delete=user_group)
    await state.set_state(DeleteGroupState.waiting_for_confirmation)

    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить группу {user_group}?\n\n"
        "❗ Напишите номер группы для подтверждения."
    )

    await callback.answer()  # Закрываем уведомление


@router.message(DeleteGroupState.waiting_for_confirmation)
async def confirm_delete_group(message: types.Message, state: FSMContext):
    """Удаление группы после подтверждения"""
    data = await state.get_data()
    group_to_delete = data.get("group_to_delete")

    if message.text.strip() != group_to_delete:
        await message.answer("❌ Название группы введено неверно. Отмена удаления.")
        await state.clear()
        return

    groups_data = await load_groups()
    if group_to_delete in groups_data:
        del groups_data[group_to_delete]
        await save_groups(groups_data)
        await message.answer(f"✅ Группа {group_to_delete} удалена из системы.")

        msg = f"Админ {message.from_user.full_name} ({message.from_user.id}) удалил из системы группу {group_to_delete}"
        write_user_log(msg)

    else:
        await message.answer("❌ Ошибка: группа не найдена.")

    await state.clear()

    # Отправляем стартовое меню отдельным сообщением
    await send_start_menu(message, new_message=True)


def _next_allowed_hour(curr: int, delta: int) -> int:
    # delta = +1 (вправо) или -1 (влево)
    idx = ALLOWED_HOURS.index(curr) if curr in ALLOWED_HOURS else 0
    return ALLOWED_HOURS[(idx + delta) % len(ALLOWED_HOURS)]


@router.callback_query(F.data == "edit_send_time")
async def handle_edit_send_time(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    groups = await load_groups()
    # находим группу старосты
    user_group = next((g for g, d in groups.items() if d.get("registered_by") == user_id), None)
    if not user_group:
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    # берём текущий час, по умолчанию 20
    current_hour = int(groups[user_group].get("send_hour", 20))
    if current_hour not in ALLOWED_HOURS:
        current_hour = 20

    await state.set_state(SendTimeState.editing)
    await state.update_data(user_group=user_group, hour=current_hour)

    try:
        await callback.message.edit_text(
            text=(
                "⏰ Время отправки расписания для вашей группы.\n"
                "Доступны только часы из окна 20:00–08:00.\n\n"
                f"Текущее время: {_fmt_hour(current_hour)}"
            ),
            reply_markup=get_edit_send_time_keyboard(current_hour)
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(SendTimeState.editing, F.data.in_(["send_time_left", "send_time_right"]))
async def change_send_time(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hour = int(data.get("hour", 20))
    delta = -1 if callback.data == "send_time_left" else +1
    new_hour = _next_allowed_hour(hour, delta)
    await state.update_data(hour=new_hour)

    try:
        await callback.message.edit_text(
            text=(
                "⏰ Время отправки расписания для вашей группы.\n"
                "Доступны только часы из окна 20:00–08:00.\n\n"
                f"Текущее время: {_fmt_hour(new_hour)}"
            ),
            reply_markup=get_edit_send_time_keyboard(new_hour)
        )
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(SendTimeState.editing, F.data == "send_time_save")
async def save_send_time(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_group = data.get("user_group")
    new_hour = int(data.get("hour", 20))

    groups = await load_groups()
    if user_group not in groups:
        await callback.answer("❌ Группа не найдена", show_alert=True)
        await state.clear()
        return

    groups[user_group]["send_hour"] = new_hour
    await save_groups(groups)  # не забудь импорт: from utils.group_utils import save_groups

    write_user_log(
        f"Админ {callback.from_user.full_name} ({callback.from_user.id}) "
        f"изменил время отправки группы {user_group} на {_fmt_hour(new_hour)}"
    )

    await state.clear()
    await callback.answer("✅ Время сохранено!", show_alert=True)

    # Вернёмся в панель
    await send_admin_panel(
        bot=callback.bot,
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        full_name=callback.from_user.full_name,
        message=callback.message,
        callback=callback
    )