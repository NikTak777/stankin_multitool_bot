from utils.database import set_user_group_subgroup
from utils.group_utils import (
    is_valid_group_name,
    is_group_file_exists,
    format_subgroup
)


def get_code_input_text() -> str:
    return (
        "Выберите код вашей группы\n"
        "   или\n"
        "Введите номер вашей группы (например, ИДБ-23-10):"
    )


def get_year_input_text() -> str:
    return "Выберите год поступления вашей группы:"


def get_group_input_text() -> str:
    return "Выберите вашу группу:"


def get_subgroup_input_text() -> str:
    return "Выберите вашу подгруппу:"


def get_save_group_text(
        user_id: int,
        group: str,
        subgroup: str,
        from_schedule: bool
) -> tuple[str, str]:
    set_user_group_subgroup(user_id, group, subgroup)
    text: str = f"✅ Новые данные успешно сохранены:\n● Группа {group},\n● Подгруппа {format_subgroup(subgroup)}."

    back_to = "schedule" if from_schedule else "info"
    if not is_group_file_exists(group):
        text += (f"\n\n⚠️ К сожалению, пока Вы не можете смотреть расписание "
                        f"Вашей группы, так как оно не появилось в системе.")
        if back_to != "info":
            back_to = "start"

    return text, back_to


def get_full_group_input_text(group: str) -> tuple[str, bool]:
    if is_valid_group_name(group):
        text: str = "Выберете вашу подгруппу:"
        is_valid: bool = True
    else:
        text: str = (
            "⚠️ Номер группы некорректный!\n\n"
            "Выберете код вашей группы\n"
            "   или\n"
            "Введите в формате XXX-00-00 (например, ИДБ-23-10):"
        )
        is_valid: bool = False
    return text, is_valid
