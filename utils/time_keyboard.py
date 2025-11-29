"""Time selection keyboard helper."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime


def create_time_keyboard() -> InlineKeyboardMarkup:
    """
    Create inline keyboard with common departure times.

    Returns:
        InlineKeyboardMarkup with time options
    """
    keyboard = []

    # Common morning times
    keyboard.append([
        InlineKeyboardButton(text="06:00", callback_data="time_06:00"),
        InlineKeyboardButton(text="07:00", callback_data="time_07:00"),
        InlineKeyboardButton(text="08:00", callback_data="time_08:00"),
    ])

    # Morning/noon times
    keyboard.append([
        InlineKeyboardButton(text="09:00", callback_data="time_09:00"),
        InlineKeyboardButton(text="10:00", callback_data="time_10:00"),
        InlineKeyboardButton(text="11:00", callback_data="time_11:00"),
    ])

    # Afternoon times
    keyboard.append([
        InlineKeyboardButton(text="12:00", callback_data="time_12:00"),
        InlineKeyboardButton(text="13:00", callback_data="time_13:00"),
        InlineKeyboardButton(text="14:00", callback_data="time_14:00"),
    ])

    # Late afternoon/evening times
    keyboard.append([
        InlineKeyboardButton(text="15:00", callback_data="time_15:00"),
        InlineKeyboardButton(text="16:00", callback_data="time_16:00"),
        InlineKeyboardButton(text="17:00", callback_data="time_17:00"),
    ])

    # Evening times
    keyboard.append([
        InlineKeyboardButton(text="18:00", callback_data="time_18:00"),
        InlineKeyboardButton(text="19:00", callback_data="time_19:00"),
        InlineKeyboardButton(text="20:00", callback_data="time_20:00"),
    ])

    # Late evening/night times
    keyboard.append([
        InlineKeyboardButton(text="21:00", callback_data="time_21:00"),
        InlineKeyboardButton(text="22:00", callback_data="time_22:00"),
        InlineKeyboardButton(text="23:00", callback_data="time_23:00"),
    ])

    # Custom time option
    keyboard.append([
        InlineKeyboardButton(text="✏️ Ввести свое время", callback_data="time_custom")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

