from utils.database_utils.friends import get_list_friends
from utils.database_utils.contest import is_active_user_in_range

async def get_friends_activity(user_id: int):
    activity: List[Dict] = []

    # friends: List[int] = get_list_friends(user_id)
    friends: List[int] = [111, 222, 333, 444, 555]
    count = 0
    for friend in friends:
        """count: int | bool = is_active_user_in_range(
            user_id=friend,
            days_range=7,
            days_count=3
        )"""
        count += 1

        activity.append(
            {
                "friend_id": friend,
                "count": count
            }
        )

    return activity
