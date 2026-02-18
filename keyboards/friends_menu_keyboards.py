from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_friends_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Список", callback_data="friends_edit_menu")],
        [InlineKeyboardButton(text="Добавить друга", callback_data="friends_request")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="start")]
    ])


def get_edit_menu_keyboard(total_friends: int, fid: int = 0, total_pages: int = 0, current_page: int = 0):
    """Создаёт клавиатуру с кнопками управления и пагинацией (при total_pages > 1)."""
    builder = InlineKeyboardBuilder()

    if total_friends == 0:
        builder.row(InlineKeyboardButton(
            text=" ◀️ Назад ",
            callback_data="friends_menu"
        ))
        return builder.as_markup()

    builder.row(
        InlineKeyboardButton(text="⬆️ Пред.", callback_data="friends_prev"),
        InlineKeyboardButton(text="След. ⬇️", callback_data="friends_next")
    )

    if total_pages > 1:
        builder.row(
            InlineKeyboardButton(text="◀️ Влево", callback_data="friends_page_prev"),
            InlineKeyboardButton(text="Вправо ▶️", callback_data="friends_page_next")
        )

    builder.row(InlineKeyboardButton(
        text="📅 Расписание",
        callback_data=f"friend_schedule_{fid}"
    ))

    builder.row(InlineKeyboardButton(
        text="📋 Профиль друга",
        callback_data="friend_profile"
    ))

    builder.row(InlineKeyboardButton(
        text="❌ Удалить друга",
        callback_data="delete_friend"
    ))

    builder.row(InlineKeyboardButton(
        text=" ◀️ Назад ",
        callback_data="friends_menu"
    ))

    return builder.as_markup()


def get_error_request_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заново", callback_data="friends_request")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="friends_menu")]
    ])


def get_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_friend_request:{request_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_friend_request:{request_id}"),
    )
    return b.as_markup()


def get_accept_request_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Список друзей", callback_data="friends_edit_menu")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="start")]
    ])


def get_wishlist_suggestion_keyboard(suggestion_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для принятия/отклонения предложения вишлиста."""
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_wishlist_suggestion:{suggestion_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_wishlist_suggestion:{suggestion_id}"),
    )
    return b.as_markup()