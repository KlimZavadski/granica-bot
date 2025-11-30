"""Keyboard utilities for bot."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def create_main_menu_keyboard(has_active_journey: bool = False) -> ReplyKeyboardMarkup:
    """
    Create main menu keyboard that is always visible.

    Args:
        has_active_journey: Whether user has an active journey

    Returns:
        ReplyKeyboardMarkup with menu options
    """
    if has_active_journey:
        buttons = [
            [KeyboardButton(text="⏰ Ввести время")],
            [KeyboardButton(text="🌍 Сменить таймзону")],
            [KeyboardButton(text="❌ Отменить поездку")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="🆕 Новая поездка")],
            [KeyboardButton(text="📊 Статистика")]
        ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True
    )


def create_cancel_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for cancel confirmation."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да, отменить", callback_data="confirm_cancel_yes"),
            InlineKeyboardButton(text="❌ Нет, продолжить", callback_data="confirm_cancel_no")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_timezone_keyboard(include_now_button: bool = False, include_cancel: bool = False) -> ReplyKeyboardMarkup:
    """
    Create keyboard for timezone selection.

    Args:
        include_now_button: Whether to include "Сейчас" button
        include_cancel: Whether to include cancel journey button
    """
    tz_buttons = [
        [KeyboardButton(text="🇧🇾 Минск (UTC+3)")],
        [KeyboardButton(text="🇵🇱 Варшава (UTC+1)")],
        [KeyboardButton(text="🇱🇹 Вильнюс (UTC+2)")],
    ]

    if include_now_button:
        tz_buttons.append([KeyboardButton(text="⏰ Сейчас (автоматически)")])

    if include_cancel:
        tz_buttons.append([KeyboardButton(text="❌ Отменить поездку")])

    return ReplyKeyboardMarkup(
        keyboard=tz_buttons,
        resize_keyboard=True,
        is_persistent=True
    )


def create_checkpoint_keyboard() -> ReplyKeyboardMarkup:
    """Create keyboard for checkpoint time entry."""
    buttons = [
        [KeyboardButton(text="⏰ Сейчас")],
        [KeyboardButton(text="🌍 Сменить таймзону")],
        [KeyboardButton(text="❌ Отменить поездку")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True
    )

