from enum import Enum
from dataclasses import dataclass

from utils.database import (
    get_user_info,
    get_id_from_username,
    check_user_by_username
)

from utils.database_utils.friends import (
    add_friend_to_user,
    add_friend_request,
    check_existing_request,
    update_friend_request_status,
    get_friend_id_from_request_id,
    check_existing_friend,
    get_list_friends
)

from services.search_profile import _parse_group, get_recommend_profiles


def get_friend_request_text(user) -> tuple[str, str]:
    user_name = user.username or "StankinMultiToolBot"
    msg_to_user = f"Введите тег пользователя, кому вы хотите отправить приглашение в друзья.\nНапример, @{user_name}\n\n"

    user_info = get_user_info(user.id)
    full_group = user_info.get('user_group') if user_info else ""

    exact_flow, direction, year = _parse_group(full_group)

    friends_ids = get_list_friends(user.id)

    recommended_users = get_recommend_profiles(
        user_id=user.id,
        exact_flow=exact_flow,
        direction=direction,
        year=year,
        exclude_ids=friends_ids
    )

    if recommended_users:
        msg_to_user += "👥 Рекомендации в друзья:\n"
        for row in recommended_users:
            tag = row[0]
            name = row[1]
            group = row[2] or "без группы"
            msg_to_user += f"• {name} (@{tag}, {group})\n"

    log_msg = f"Пользователь {user.full_name} ({user.id}) @{user.username} начал ввод юзернейма пользователя для добавления в друзья"
    return msg_to_user, log_msg


class FriendRequestStatus(Enum):
    INVALID = "invalid"
    SELF_ADD = "self_add"
    NOT_FOUND = "not_found"
    ALREADY_FRIENDS = "already_friends"
    REQUEST_EXISTS = "request_exists"
    BOT_BLOCKED = "bot_blocked"
    ERROR = "error"
    SUCCESS = "success"

INVALID_TEXT = "❌ Юзернейм должен содержать от 2 до 50 символов.\n\nПопробуйте ввести ещё раз или нажмите «Отмена»."
SELF_ADD_TEXT = "❌ Себя нельзя добавить в друзья."
NOT_FOUND_TEXT = "❌ Пользователь не найден.\n\nВозможно, он ещё не пользовался ботом или делал это очень давно."


def create_friend_request(
        search_username: str,
        own_username: str,
        own_user_id: int
) -> tuple[FriendRequestStatus, str, int | None, int | None]:
    """
    return:
        FriendRequestStatus,
        text to send to user,
        request id of friend request,
        friend id of friend request,
    """
    search_username = search_username.strip().lstrip("@")

    if not (3 <= len(search_username) <= 50):
        return FriendRequestStatus.INVALID, INVALID_TEXT, None, None

    if search_username == own_username:
        return FriendRequestStatus.SELF_ADD, SELF_ADD_TEXT, None, None

    if not check_user_by_username(search_username):
        return FriendRequestStatus.NOT_FOUND, NOT_FOUND_TEXT, None, None

    friend_id = get_id_from_username(search_username)[0]
    receive_name = get_user_info(friend_id)["user_name"]

    if check_existing_friend(own_user_id, friend_id):
        return (
            FriendRequestStatus.ALREADY_FRIENDS,
            f"⚠️ Вы уже являетесь друзьями с {receive_name}.",
            None,
            friend_id
        )

    if check_existing_request(own_user_id, friend_id):
        return (
            FriendRequestStatus.REQUEST_EXISTS,
            f"⚠️ Вы уже отправили запрос пользователю {receive_name}.",
            None,
            friend_id
        )

    request_id = add_friend_request(own_user_id, friend_id)
    return (
        FriendRequestStatus.SUCCESS,
        f"✅ Ваш запрос пользователю {receive_name} был успешно отправлен!\n"
        f"Вам придёт уведомление, когда будет ответ.",
        request_id,
        friend_id
    )

@dataclass(slots=True)
class FriendRequestResult():
    receiver_req_text: str
    sender_req_text: str
    log_text: str
    sender_id: int
    is_accepted: bool


def process_friend_request_action(
        receiver_id: int,
        request_id: int,
        is_accepted: bool
) -> FriendRequestResult:
    """
    params:
        receiver_id - id пользователя, получившего приглашение
        request_id - id приглашения из кнопки
        is_accepted - принято приглашение или нет (отклонено)
    returns:
        FriendRequestResult(
            receiver_req_text - текст сообщения пользователю, получившего приглашение
            sender_req_text - текст сообщения пользователю, отправившего приглашение
            log_text - текст для логирования
            sender_id - id пользователя, отправившего приглашение
            is_accepted - принято приглашение или нет (отклонено)
        )
    """
    sender_id = get_friend_id_from_request_id(request_id)
    sender_info = get_user_info(sender_id)
    sender_fullname, sender_username = sender_info["user_name"], sender_info["user_tag"]

    receiver_info = get_user_info(receiver_id)
    receiver_fullname, receiver_username = receiver_info["user_name"], receiver_info["user_tag"]

    if is_accepted:
        update_friend_request_status(request_id, "accepted")
        add_friend_to_user(receiver_id, sender_id)
        add_friend_to_user(sender_id, receiver_id)

        receiver_req_text = f"Вы стали друзьями c пользователем {sender_fullname} @{sender_username}!"
        sender_req_text = f"Пользователь {receiver_fullname} @{receiver_username} принял Ваш запрос в друзья!"
        log_text = (f"Пользователь {receiver_fullname} ({receiver_id}) @{receiver_username} "
                    f"принял запрос пользователя {sender_fullname} ({sender_id}) @{sender_username}")
    else:
        update_friend_request_status(request_id, "declined")

        receiver_req_text = f"Вы отклонили запрос пользователя {sender_fullname} @{sender_username}!"
        sender_req_text = f"Пользователь {receiver_fullname} @{receiver_username} отклонил Ваш запрос в друзья!"
        log_text = (f"Пользователь {receiver_fullname} ({receiver_id}) @{receiver_username} "
                    f"отклонил запрос пользователя {sender_fullname} ({sender_id}) @{sender_username}")


    return FriendRequestResult(
        receiver_req_text=receiver_req_text,
        sender_req_text=sender_req_text,
        log_text=log_text,
        sender_id=sender_id,
        is_accepted=is_accepted
    )















