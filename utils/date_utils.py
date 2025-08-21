def format_date(day, month, year=None):
    if year is None:
        return f"{day:02}.{month:02}"
    return f"{day:02}.{month:02}.{year}"