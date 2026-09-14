from utils.db_connection import get_db_connection


def get_recommend_profiles(
        user_id: int,
        exact_flow: str,
        direction: str,
        year: str,
        limit: int = 5,
        exclude_ids: list[int] | None = None,
) -> list[tuple]:
    """
    Ищет профили, сортируя их по степени релевантности группы (поток -> направление/год -> случайные).
    Пропускает список профилей из exclude_ids.
    """
    if exclude_ids is None:
        exclude_ids = []

    exclude_ids.append(user_id)
    exclude_tuple = tuple(set(exclude_ids))

    with get_db_connection() as con:
        cur = con.cursor()

        mask_exact = f"{exact_flow}%"  # ИДБ-23%
        mask_dir = f"{direction}-%"  # ИДБ-%
        mask_year = f"%-{year}-%"  # %-23-%

        cur.execute("""
            SELECT user_tag, user_name, user_group
            FROM users
            WHERE user_id NOT IN %s 
              AND user_tag IS NOT NULL
            ORDER BY 
                CASE 
                    WHEN user_group LIKE %s THEN 1
                    WHEN user_group LIKE %s THEN 2
                    WHEN user_group LIKE %s THEN 2
                    ELSE 3
                END ASC,
                RANDOM()
            LIMIT %s
        """, (exclude_tuple, mask_exact, mask_dir, mask_year, limit))

        return cur.fetchall()