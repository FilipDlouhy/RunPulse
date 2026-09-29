from datetime import timedelta


def week_start(day):
    return day - timedelta(days=day.weekday())
