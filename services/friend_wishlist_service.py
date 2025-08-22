# services/friend_wishlist_service.py
def birthday_missing_text() -> str:
    return (
        "Вишлист не может быть выведен, так как вы не указали свою дату рождения.\n"
        "Пожалуйста, используйте команду /birthdate для создания аккаунта."
    )

def friend_wishlist_prompt(user_tag: str | None) -> str:
    if user_tag:
        return (
            f"Пожалуйста, введите тег пользователя, чей вишлист вы хотите посмотреть.\n"
            f"Например, @{user_tag}"
        )
    return (
        "Пожалуйста, введите тег пользователя, чей вишлист вы хотите посмотреть.\n"
        "Например, @StankinMultiToolBot"
    )

def own_wishlist_message(user_wishlist: str | None) -> str:
    if not user_wishlist:
        return "Кажется, вы ещё не составили свой вишлист. Напишите команду /my_wishlist, чтобы добавить желания."
    return f"Вот ваш текущий вишлист: {user_wishlist}"

def friend_wishlist_not_found(friend_tag: str) -> str:
    return f"Пользователь с тегом @{friend_tag} не найден."

def friend_wishlist_empty(friend_name: str, friend_tag: str) -> str:
    return f"Пользователь {friend_name} @{friend_tag} ещё не составил вишлист. Напомните ему об этом!"

def friend_wishlist_info(friend_name: str, friend_tag: str, friend_wishlist: str) -> str:
    return f"Вишлист пользователя {friend_name} @{friend_tag}:\n{friend_wishlist}"
