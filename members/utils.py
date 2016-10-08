from django.conf import settings


def first_season():
    return 2012


def current_season():
    today = settings.NOW().date()
    if today.month >= 9:
        return today.year + 1
    return today.year
