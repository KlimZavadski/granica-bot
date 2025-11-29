"""Calendar keyboard for date selection."""
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from calendar import monthrange


def create_calendar(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard calendar.

    Args:
        year: Year to display (default: current)
        month: Month to display (default: current)

    Returns:
        InlineKeyboardMarkup with calendar
    """
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    # Month name
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    keyboard = []

    # Header with month/year and navigation
    keyboard.append([
        InlineKeyboardButton(text="<", callback_data=f"cal_prev_{year}_{month}"),
        InlineKeyboardButton(text=f"{month_names[month-1]} {year}", callback_data="cal_ignore"),
        InlineKeyboardButton(text=">", callback_data=f"cal_next_{year}_{month}")
    ])

    # Days of week header
    keyboard.append([
        InlineKeyboardButton(text="Пн", callback_data="cal_ignore"),
        InlineKeyboardButton(text="Вт", callback_data="cal_ignore"),
        InlineKeyboardButton(text="Ср", callback_data="cal_ignore"),
        InlineKeyboardButton(text="Чт", callback_data="cal_ignore"),
        InlineKeyboardButton(text="Пт", callback_data="cal_ignore"),
        InlineKeyboardButton(text="Сб", callback_data="cal_ignore"),
        InlineKeyboardButton(text="Вс", callback_data="cal_ignore")
    ])

    # Get first day of month and number of days
    first_weekday = datetime(year, month, 1).weekday()  # 0 = Monday
    num_days = monthrange(year, month)[1]

    # Build calendar grid
    week = []
    # Empty cells before first day
    for _ in range(first_weekday):
        week.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))

    # Days of month
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        # Disable past dates
        if date.date() < now.date():
            week.append(InlineKeyboardButton(text=str(day), callback_data="cal_ignore"))
        else:
            week.append(InlineKeyboardButton(
                text=str(day),
                callback_data=f"cal_day_{year}_{month}_{day}"
            ))

        # If week is full (7 days), add to keyboard and start new week
        if len(week) == 7:
            keyboard.append(week)
            week = []

    # Fill remaining cells in last week
    if week:
        while len(week) < 7:
            week.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))
        keyboard.append(week)

    # Cancel button
    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cal_cancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_next_month(year: int, month: int) -> tuple[int, int]:
    """Get next month/year."""
    if month == 12:
        return year + 1, 1
    return year, month + 1


def get_prev_month(year: int, month: int) -> tuple[int, int]:
    """Get previous month/year."""
    if month == 1:
        return year - 1, 12
    return year, month - 1

