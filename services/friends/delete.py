from utils.database_utils.friends import get_friends_info, delete_friend
from dataclasses import dataclass


@dataclass(slots=True)
class FriendDeleteResult:
    status: str
    index: int
    prefix_msg: str
    alert: str
    friend_name: str | None
    friend_id: int | None


def delete_friend_service(user_id: int, index: int) -> FriendDeleteResult:
    friend_pairs = get_friends_info(user_id)
    total = len(friend_pairs)

    if total == 0:
        return FriendDeleteResult(
            status="not_found",
            index=0,
            prefix_msg="",
            alert="❌ Ошибка удаления",
            friend_name=None,
            friend_id=None
        )

    if index >= total: index = 0

    friend_id, friend_name = friend_pairs[index]
    delete_friend(user_id, friend_id)
    delete_friend(friend_id, user_id)

    upd_friend_pairs = get_friends_info(user_id)
    upd_total = len(upd_friend_pairs)

    if upd_total == 0:
        return FriendDeleteResult(
            status="delete_last",
            index=0,
            prefix_msg=f"🗑 Друг «{friend_name}» удалён.\n\n",
            alert=f"🗑 Удалён «{friend_name}»",
            friend_name=friend_name,
            friend_id=friend_id
        )

    if index >= upd_total and upd_total > 0:
        index = upd_total - 1

    return FriendDeleteResult(
        status="success",
        index=index,
        prefix_msg=f"🗑 Друг «{friend_name}» удалён.\n\n",
        alert=f"🗑 Удалён «{friend_name}»",
        friend_name=friend_name,
        friend_id=friend_id
    )