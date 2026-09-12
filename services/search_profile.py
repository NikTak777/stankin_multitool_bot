from utils.database_utils.recommendation_users import get_recommend_profiles
from utils.database import get_id_from_username, get_user_info
from utils.date_utils import format_date

COUNT_RECOMMEND_PROFILES: int = 5


def get_search_profile_msg(user) -> str:
    safe_name = user.username or "StankinMultiToolBot"
    msg_to_user = (
        f"Введите юзернейм пользователя, чей профиль вы хотите посмотреть.\n"
        f"Например, @{safe_name}\n\n"
    )

    user_info = get_user_info(user.id)
    full_group = user_info.get('user_group') if user_info else ""

    exact_flow, direction, year = _parse_group(full_group)

    recommended_users = get_recommend_profiles(
        user_id=user.id,
        exact_flow=exact_flow,
        direction=direction,
        year=year,
        limit=COUNT_RECOMMEND_PROFILES
    )

    if recommended_users:
        msg_to_user += "👥 Рекомендованные пользователи:\n"
        for row in recommended_users:
            tag = row[0]
            name = row[1]
            group = row[2] or "без группы"
            msg_to_user += f"• {name} (@{tag}, {group})\n"

    return msg_to_user


def get_user_profile_msg(user_name: str, called_user_id: int) -> tuple[bool, str]:
    user_id = get_id_from_username(user_name)
    if user_id == "not_found" or not user_id:
        return False, get_user_not_found_text(user_name)

    user_id = user_id[0]
    user_info = get_user_info(user_id)

    day, month, year = user_info["user_day"], user_info["user_month"], user_info["user_year"]
    if not day or not month or not year:
        birthdate = "Отсутствует"
    else:
        birthdate = format_date(day, month, year)

    wishlist = user_info["user_wishlist"] or "Отсутствует"
    group = user_info["user_group"] or "Отсутствует"
    subgroup = user_info["user_subgroup"] or "Отсутствует"
    subgroup = {"A": "А", "B": "Б"}.get(subgroup, subgroup)

    user_profile: str = ""
    if called_user_id == user_id:
        user_profile += "Хм, вы ввели свой собственный юзернейм. Пытаетесь проверить сами себя? 😉\n\nВаш профиль:\n"
    else:
        user_profile += f"Профиль пользователя @{user_name}:\n"

    user_profile += (
        f"🎂 Дата рождения: {birthdate}\n"
        f"🎁 Вишлист: {wishlist}\n"
        f"🏫 Группа: {group}\n"
        f"📚 Подгруппа: {subgroup}"
    )

    return True, user_profile


def get_invalid_username_text() -> str:
    return "❌ Юзернейм должен содержать от 2 до 50 символов.\n\nПопробуйте ввести ещё раз или нажмите «Отмена»."


def get_user_not_found_text(user_name: str) -> str:
    return f"❌ Пользователь с тегом @{user_name} не найден.\n\nВозможно он ещё не пользовался ботом или делал это очень давно."


def _parse_group(full_group: str) -> tuple[str, str, str]:
    """
    Разбивает группу на (поток, направление, год).
    Пример: 'ИДБ-23-10' -> ('ИДБ-23', 'ИДБ', '23')
    """
    if not full_group:
        return "", "", ""

    parts = full_group.split('-')
    if len(parts) >= 2:
        exact_flow = f"{parts[0]}-{parts[1]}"
        direction = parts[0]
        year = parts[1]
        return exact_flow, direction, year

    return "", "", ""