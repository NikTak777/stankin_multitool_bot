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
from utils.logger import write_user_log
from utils.database import get_users_by_group, get_approval_status, toggle_user_approval, update_real_user_name

router = Router()

@router.message(Command("panel"))
async def admin_panel(message: types.Message):

    if message.chat.type != "private":
        await message.answer("❌ Эта команда доступна только в личной переписке с ботом.")
        return

    UserID = message.from_user.id
    groups = await load_groups()

    # Проверяем, является ли пользователь старостой
    user_group = next((group for group, data in groups.items() if data["registered_by"] == UserID), None)

    if not user_group:
        await message.answer("❌ У вас нет доступа к панели управления, так как вы не зарегистрированы как староста.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать группу", callback_data="edit_group")],
        [InlineKeyboardButton(text="🗑 Удалить регистрацию", callback_data="delete_group")]
    ])

    text = (
        f"Привет, {message.from_user.full_name}!\n"
        "Это панель управления вашей группой.\n\n"
        f"📌 Вы являетесь старостой группы {user_group}\n\n"
        "Выберите действие:"
    )

    msg = f"Админ {message.from_user.full_name} ({message.from_user.id}) открыл панель управления группой {user_group}"
    write_user_log(msg)

    await message.answer(text, reply_markup=keyboard)


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
            "Редактирование группы завершено",
            reply_markup=None
        )
        groups = await load_groups()
        user_group = next((group for group, data in groups.items() if data["registered_by"] == callback.from_user.id), None)
        msg = f"Админ {callback.from_user.full_name} ({callback.from_user.id}) закрыл панель управления группой {user_group}"
        write_user_log(msg)
    except TelegramBadRequest:
        pass


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