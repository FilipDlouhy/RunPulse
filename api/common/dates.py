from datetime import timedelta


def week_start(day):
    """Return the Monday of the week containing the given date."""
    return day - timedelta(days=day.weekday())
