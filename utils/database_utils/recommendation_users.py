from utils.db_connection import get_db_connection


def get_recommend_profiles(
        user_id: int,
        exact_flow: str,
        direction: str,
        year: str,
        limit: int = 5
) -> list[tuple]:
    """
    Ищет профили, сортируя их по степени релевантности группы (поток -> направление/год -> случайные).
    """
    with get_db_connection() as con:
        cur = con.cursor()

        mask_exact = f"{exact_flow}%"  # ИДБ-23%
        mask_dir = f"{direction}-%"  # ИДБ-%
        mask_year = f"%-{year}-%"  # %-23-%

        cur.execute("""
            SELECT user_tag, user_name, user_group
            FROM users
            WHERE user_id != %s 
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
        """, (user_id, mask_exact, mask_dir, mask_year, limit))

        return cur.fetchall()