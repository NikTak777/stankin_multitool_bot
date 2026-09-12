from utils.search_profile import get_recommend_profiles

COUNT_RECOMMEND_PROFILES: int = 5


def get_search_profile_msg(user) -> str:
    user_name = user.username or "StankinMultiToolBot"

    msg_to_user: str = (f"Пожалуйста, введите тег пользователя, "
                f"чей профиль вы хотите посмотреть.\n"
                f"Например, @{user_name}")


    profiles_list: str = "Рекомендованные пользователи:\n"
    get_recommend_profiles(
        user_id=user.id,
        count=COUNT_RECOMMEND_PROFILES
    )
    msg_to_user += profiles_list
    return msg_to_user
