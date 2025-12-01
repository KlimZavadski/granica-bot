"""Journey tracking handlers."""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime
from typing import List, Dict, Any

from .states import JourneyStates
from database import db
from utils import (
    now_utc,
    parse_user_datetime,
    parse_checkpoint_time,
    format_datetime_for_user,
    validate_checkpoint_order,
    parse_db_timestamp,
    create_calendar,
    get_next_month,
    get_prev_month,
    create_time_keyboard,
    create_main_menu_keyboard,
    create_cancel_confirmation_keyboard,
    create_timezone_keyboard,
    create_checkpoint_keyboard
)

router = Router()

# Checkpoint display names
CHECKPOINT_NAMES = {
    "approaching_border": "🚌 Подъехали к шлагбауму",
    "entering_checkpoint_1": "🛂 Въезд на КПП #1",
    "invited_passport_control_1": "✅ Прошли паспортный контроль #1",  # Legacy name
    "passed_passport_control_1": "✅ Прошли паспортный контроль #1",   # New name
    "entering_checkpoint_2": "🛂 Въезд на КПП #2",
    "invited_passport_control_2": "✅ Прошли паспортный контроль #2",  # Legacy name
    "passed_passport_control_2": "✅ Прошли паспортный контроль #2",   # New name
    "leaving_checkpoint_2": "🏁 Покидаем границу"
}

# Timezone mapping
TIMEZONE_MAP = {
    "🇧🇾 Минск (UTC+3)": "Europe/Minsk",
    "🇵🇱 Варшава (UTC+1)": "Europe/Warsaw",
    "🇱🇹 Вильнюс (UTC+2)": "Europe/Vilnius"
}

# Reverse mapping for display
TIMEZONE_DISPLAY = {
    "Europe/Minsk": "🇧🇾 Минск (UTC+3)",
    "Europe/Warsaw": "🇵🇱 Варшава (UTC+1)",
    "Europe/Vilnius": "🇱🇹 Вильнюс (UTC+2)"
}


def get_timezone_display(timezone: str) -> str:
    """Get display name for timezone."""
    return TIMEZONE_DISPLAY.get(timezone, timezone)


def create_carrier_keyboard(carriers: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """Create keyboard with carrier options."""
    buttons = [[KeyboardButton(text=carrier["name"])] for carrier in carriers]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command - show welcome and instructions."""
    # Check if user has active journey
    active_journey = await db.get_user_active_journey(message.from_user.id)

    welcome_text = (
        "👋 Добро пожаловать в Granica Bot!\n\n"
        "Этот бот помогает отслеживать время прохождения границы между Беларусью и Польшей/Литвой.\n\n"
        "📝 Как это работает:\n"
        "1. Выберите перевозчика\n"
        "2. Укажите время отправления\n"
        "3. Отмечайте контрольные точки по мере прохождения\n"
        "4. Просматривайте статистику и помогайте другим планировать поездки\n\n"
        "⚡️ Быстрые команды:\n"
        "/new — начать новую поездку\n"
        "/statistics — посмотреть статистику\n\n"
        "Используйте меню внизу для навигации"
    )

    keyboard = create_main_menu_keyboard(has_active_journey=active_journey is not None)
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("new"))
@router.message(F.text == "🆕 Новая поездка")
async def cmd_new_journey(message: Message, state: FSMContext):
    """Start a new journey."""
    # Check if user has an active journey
    active_journey = await db.get_user_active_journey(message.from_user.id)
    if active_journey:
        keyboard = create_main_menu_keyboard(has_active_journey=True)
        await message.answer(
            "⚠️ У вас уже есть активная поездка.\n\n"
            "Используйте кнопку '⏰ Ввести время' чтобы продолжить,\n"
            "или '❌ Отменить поездку' чтобы начать новую.",
            reply_markup=keyboard
        )
        return

    # Get carriers from database
    carriers = await db.get_carriers()
    keyboard = create_carrier_keyboard(carriers)

    await state.set_state(JourneyStates.choosing_carrier)

    # Send main accumulating message
    main_msg = await message.answer(
        "🆕 Новая поездка\n\n"
        "🚌 Выберите перевозчика:",
        reply_markup=keyboard
    )

    # Save main message ID for future edits
    await state.update_data(main_message_id=main_msg.message_id)


@router.message(JourneyStates.choosing_carrier)
async def process_carrier_choice(message: Message, state: FSMContext):
    """Process carrier selection."""
    # Check if user wants to cancel
    if message.text == "❌ Отменить поездку":
        await cmd_cancel(message, state)
        return

    carriers = await db.get_carriers()
    carrier = next((c for c in carriers if c["name"] == message.text), None)

    if not carrier:
        await message.answer("❌ Неверный перевозчик. Пожалуйста, выберите из списка.")
        return

    await state.update_data(carrier_id=carrier["id"], carrier_name=carrier["name"])
    await state.set_state(JourneyStates.entering_departure_date)

    # Get main message ID
    data = await state.get_data()
    main_message_id = data.get("main_message_id")

    # Delete user's choice message
    try:
        await message.delete()
    except Exception:
        pass

    # Delete the initial question message
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=main_message_id
        )
    except Exception as e:
        print(f"Error deleting message: {e}")

    # Create new message with accumulated data
    calendar = create_calendar()
    msg = await message.answer(
        "🆕 Новая поездка\n\n"
        f"✅ Перевозчик: {carrier['name']}\n\n"
        "📅 Выберите дату отправления:",
        reply_markup=calendar
    )
    # Update main message ID
    await state.update_data(main_message_id=msg.message_id)

    # Send temporary message to remove keyboard, then delete it
    try:
        temp_msg = await message.answer(".", reply_markup=ReplyKeyboardRemove())
        await temp_msg.delete()
    except Exception:
        pass


# Calendar callback handlers
@router.callback_query(F.data.startswith("cal_"))
async def process_calendar_callback(callback: CallbackQuery, state: FSMContext):
    """Process calendar button callbacks."""
    print(f"📅 Calendar callback: {callback.data}")

    current_state = await state.get_state()
    print(f"Current state: {current_state}")

    # Only handle calendar in date selection state
    if current_state != JourneyStates.entering_departure_date:
        print(f"⚠️ Wrong state, ignoring callback")
        await callback.answer()
        return

    data = callback.data.split("_")
    action = data[1]
    print(f"Action: {action}")

    if action == "ignore":
        await callback.answer()
        return

    elif action == "cancel":
        await callback.answer()
        await state.clear()
        try:
            await callback.message.edit_text(
                "❌ Отменено. Используйте /new чтобы начать заново."
            )
        except Exception:
            await callback.message.delete()
            await callback.bot.send_message(
                callback.message.chat.id,
                "❌ Отменено. Используйте /new чтобы начать заново."
            )
        return

    elif action == "prev":
        year, month = int(data[2]), int(data[3])
        prev_year, prev_month = get_prev_month(year, month)
        calendar = create_calendar(prev_year, prev_month)
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=calendar)
        return

    elif action == "next":
        year, month = int(data[2]), int(data[3])
        next_year, next_month = get_next_month(year, month)
        calendar = create_calendar(next_year, next_month)
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=calendar)
        return

    elif action == "day":
        print(f"📅 Day selected!")
        year, month, day = int(data[2]), int(data[3]), int(data[4])
        selected_date = f"{year:04d}-{month:02d}-{day:02d}"
        print(f"Selected date: {selected_date}")

        await state.update_data(departure_date=selected_date)
        print(f"✅ State updated with date")

        await state.set_state(JourneyStates.entering_departure_time)
        print(f"✅ State changed to entering_departure_time")

        time_keyboard = create_time_keyboard()
        print(f"✅ Time keyboard created")

        # Answer callback first to remove loading state
        await callback.answer()
        print(f"✅ Callback answered")

        # Get accumulated data
        state_data = await state.get_data()
        carrier_name = state_data.get("carrier_name", "")

        try:
            # Edit the main message with accumulated info
            print(f"📝 Trying to edit message...")
            await callback.message.edit_text(
                "🆕 Новая поездка\n\n"
                f"✅ Перевозчик: {carrier_name}\n"
                f"✅ Дата выбрана: {day:02d}.{month:02d}.{year}\n\n"
                "🕐 Выберите время отправления:",
                reply_markup=time_keyboard
            )
            print(f"✅ Message edited successfully!")
        except Exception as e:
            # If edit fails, send new message
            print(f"❌ Error editing message: {e}")
            print(f"📤 Sending new message instead...")
            await callback.message.delete()
            msg = await callback.bot.send_message(
                callback.message.chat.id,
                "🆕 Новая поездка\n\n"
                f"✅ Перевозчик: {carrier_name}\n"
                f"✅ Дата выбрана: {day:02d}.{month:02d}.{year}\n\n"
                "🕐 Выберите время отправления:",
                reply_markup=time_keyboard
            )
            # Update main message ID
            await state.update_data(main_message_id=msg.message_id)
            print(f"✅ New message sent!")


@router.message(JourneyStates.entering_departure_date)
async def process_departure_date_text(message: Message, state: FSMContext):
    """Handle text input in date selection state (fallback)."""
    await message.answer(
        "⚠️ Пожалуйста, используйте календарь выше для выбора даты."
    )


# Time selection callback handlers
@router.callback_query(F.data.startswith("time_"))
async def process_time_callback(callback: CallbackQuery, state: FSMContext):
    """Process time selection button callbacks."""
    print(f"🕐 Time callback: {callback.data}")

    current_state = await state.get_state()
    print(f"Current state: {current_state}")

    if current_state != JourneyStates.entering_departure_time:
        print(f"⚠️ Wrong state, ignoring callback")
        await callback.answer()
        return

    time_str = callback.data.replace("time_", "")
    print(f"Selected time: {time_str}")

    # Answer callback first
    await callback.answer()

    if time_str == "custom":
        # Get accumulated data
        state_data = await state.get_data()
        carrier_name = state_data.get("carrier_name", "")
        dep_date = state_data.get("departure_date", "")
        year, month, day = dep_date.split("-")
        date_formatted = f"{day}.{month}.{year}"

        # Switch to manual time entry
        try:
            await callback.message.edit_text(
                "🆕 Новая поездка\n\n"
                f"✅ Перевозчик: {carrier_name}\n"
                f"✅ Дата выбрана: {date_formatted}\n\n"
                "✏️ Введите время отправления вручную (ЧЧ:ММ):\n"
                "Пример: 14:30"
            )
        except Exception:
            await callback.message.delete()
            msg = await callback.bot.send_message(
                callback.message.chat.id,
                "🆕 Новая поездка\n\n"
                f"✅ Перевозчик: {carrier_name}\n"
                f"✅ Дата выбрана: {date_formatted}\n\n"
                "✏️ Введите время отправления вручную (ЧЧ:ММ):\n"
                "Пример: 14:30"
            )
            # Update main message ID
            await state.update_data(main_message_id=msg.message_id)
        return

    # Process selected time
    data = await state.get_data()

    # Parse and convert to UTC
    departure_utc = parse_user_datetime(
        data["departure_date"],
        time_str,
        "Europe/Minsk"  # Default to Belarus timezone
    )

    # Create journey in database
    journey = await db.create_journey(
        user_id=callback.from_user.id,
        carrier_id=data["carrier_id"],
        departure_utc=departure_utc
    )

    await state.update_data(
        journey_id=journey["id"],
        departure_time=time_str,
        current_checkpoint_index=0
    )

    # Get mandatory checkpoints
    checkpoints = await db.get_mandatory_checkpoints()
    await state.update_data(checkpoints=[cp["id"] for cp in checkpoints])

    # Ask for timezone
    await state.set_state(JourneyStates.choosing_initial_timezone)
    keyboard = create_timezone_keyboard(include_cancel=True)

    # Format date nicely
    dep_date = data["departure_date"]
    year, month, day = dep_date.split("-")
    date_formatted = f"{day}.{month}.{year}"

    # Delete previous message (can't edit with ReplyKeyboardMarkup)
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

    # Send new message
    msg = await callback.bot.send_message(
        callback.message.chat.id,
        "🆕 Новая поездка\n\n"
        f"✅ Перевозчик: {data['carrier_name']}\n"
        f"✅ Дата: {date_formatted}\n"
        f"✅ Время: {time_str}\n\n"
        f"🌍 Выберите вашу текущую таймзону:\n"
        f"(Вы сможете изменить её в любой момент)",
        reply_markup=keyboard
    )
    # Update main message ID
    await state.update_data(main_message_id=msg.message_id)


@router.message(JourneyStates.entering_departure_time)
async def process_departure_time(message: Message, state: FSMContext):
    """Process departure time (manual text input)."""
    # Check if user wants to cancel
    if message.text == "❌ Отменить поездку":
        await cmd_cancel(message, state)
        return

    try:
        datetime.strptime(message.text, "%H:%M")
        data = await state.get_data()

        # Parse and convert to UTC
        departure_utc = parse_user_datetime(
            data["departure_date"],
            message.text,
            "Europe/Minsk"  # Default to Belarus timezone
        )

        # Create journey in database
        journey = await db.create_journey(
            user_id=message.from_user.id,
            carrier_id=data["carrier_id"],
            departure_utc=departure_utc
        )

        await state.update_data(
            journey_id=journey["id"],
            departure_time=message.text,
            current_checkpoint_index=0
        )

        # Get mandatory checkpoints
        checkpoints = await db.get_mandatory_checkpoints()
        await state.update_data(checkpoints=[cp["id"] for cp in checkpoints])

        # Ask for timezone
        await state.set_state(JourneyStates.choosing_initial_timezone)
        keyboard = create_timezone_keyboard(include_cancel=True)

        # Format date nicely
        dep_date = data["departure_date"]
        year, month, day = dep_date.split("-")
        date_formatted = f"{day}.{month}.{year}"

        # Delete user's input message
        try:
            await message.delete()
        except Exception:
            pass

        # Get main message ID and delete it
        main_message_id = data.get("main_message_id")
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=main_message_id
            )
        except Exception as e:
            print(f"Error deleting message: {e}")

        # Send new message (can't edit with ReplyKeyboardMarkup)
        msg = await message.answer(
            "🆕 Новая поездка\n\n"
            f"✅ Перевозчик: {data['carrier_name']}\n"
            f"✅ Дата: {date_formatted}\n"
            f"✅ Время: {message.text}\n\n"
            f"🌍 Выберите вашу текущую таймзону:\n"
            f"(Вы сможете изменить её в любой момент)",
            reply_markup=keyboard
        )
        # Update main message ID
        await state.update_data(main_message_id=msg.message_id)

    except ValueError:
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ (например, 14:30)")


async def start_next_checkpoint(message_or_callback, state: FSMContext):
    """Start recording next checkpoint."""
    data = await state.get_data()
    checkpoint_index = data["current_checkpoint_index"]
    checkpoints = await db.get_mandatory_checkpoints()

    if checkpoint_index >= len(checkpoints):
        # All mandatory checkpoints done
        await show_journey_summary(message_or_callback, state)
        return

    checkpoint = checkpoints[checkpoint_index]
    checkpoint_name = CHECKPOINT_NAMES.get(checkpoint["name"], checkpoint["name"])

    # Map checkpoint to state
    state_mapping = {
        0: JourneyStates.checkpoint_approaching_border,
        1: JourneyStates.checkpoint_entering_1,
        2: JourneyStates.checkpoint_passport_1,
        3: JourneyStates.checkpoint_entering_2,
        4: JourneyStates.checkpoint_passport_2,
        5: JourneyStates.checkpoint_leaving_2,
    }

    await state.set_state(state_mapping[checkpoint_index])
    await state.update_data(current_checkpoint_id=checkpoint["id"])

    keyboard = create_checkpoint_keyboard()

    # Get current timezone to display
    current_tz = data.get("user_timezone", "Europe/Minsk")
    tz_display = get_timezone_display(current_tz)

    # Handle both Message and CallbackQuery
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(
            f"📍 Контрольная точка {checkpoint_index + 1}/6\n{checkpoint_name}\n\n"
            f"🌍 Таймзона: {tz_display}\n"
            f"⏰ Введите время (ЧЧ:ММ) или нажмите '⏰ Сейчас':",
            reply_markup=keyboard
        )
    else:  # CallbackQuery
        await message_or_callback.bot.send_message(
            message_or_callback.message.chat.id,
            f"📍 Контрольная точка {checkpoint_index + 1}/6\n{checkpoint_name}\n\n"
            f"🌍 Таймзона: {tz_display}\n"
            f"⏰ Введите время (ЧЧ:ММ) или нажмите '⏰ Сейчас':",
            reply_markup=keyboard
        )


@router.message(JourneyStates.choosing_initial_timezone)
async def process_initial_timezone_selection(message: Message, state: FSMContext):
    """Process initial timezone selection after journey creation."""
    # Check if user wants to cancel
    if message.text == "❌ Отменить поездку":
        await cmd_cancel(message, state)
        return

    # Check if valid timezone selected
    if message.text in TIMEZONE_MAP:
        selected_tz = TIMEZONE_MAP[message.text]

        # Save timezone
        await state.update_data(user_timezone=selected_tz)

        # Delete user's choice message
        try:
            await message.delete()
        except Exception:
            pass

        # Get accumulated data
        data = await state.get_data()
        main_message_id = data.get("main_message_id")

        # Format date nicely
        dep_date = data["departure_date"]
        year, month, day = dep_date.split("-")
        date_formatted = f"{day}.{month}.{year}"

        # Delete old message (can't edit ReplyKeyboardMarkup messages)
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=main_message_id
            )
        except Exception as e:
            print(f"Error deleting message: {e}")

        # Send new message with summary
        msg = await message.answer(
            "🆕 Новая поездка\n\n"
            f"✅ Перевозчик: {data['carrier_name']}\n"
            f"✅ Дата: {date_formatted}\n"
            f"✅ Время: {data['departure_time']}\n"
            f"✅ Таймзона: {message.text}\n\n"
            f"Теперь отмечайте контрольные точки по мере прохождения."
        )
        # Update main message ID
        await state.update_data(main_message_id=msg.message_id)

        # Move to first checkpoint
        await start_next_checkpoint(message, state)
    else:
        await message.answer(
            "❌ Пожалуйста, выберите таймзону из предложенных вариантов."
        )


@router.message(JourneyStates.changing_timezone)
async def process_timezone_change(message: Message, state: FSMContext):
    """Process timezone change during active journey."""
    data = await state.get_data()

    # Check if valid timezone selected
    if message.text in TIMEZONE_MAP:
        selected_tz = TIMEZONE_MAP[message.text]

        # Save new timezone
        await state.update_data(user_timezone=selected_tz)

        # Return to previous checkpoint state
        checkpoint_index = data.get("current_checkpoint_index", 0)
        checkpoints = await db.get_mandatory_checkpoints()

        if checkpoint_index >= len(checkpoints):
            # Journey already completed
            keyboard = create_main_menu_keyboard(has_active_journey=False)
            await message.answer(
                f"✅ Таймзона изменена: {message.text}",
                reply_markup=keyboard
            )
            return

        # Map checkpoint to state
        state_mapping = {
            0: JourneyStates.checkpoint_approaching_border,
            1: JourneyStates.checkpoint_entering_1,
            2: JourneyStates.checkpoint_passport_1,
            3: JourneyStates.checkpoint_entering_2,
            4: JourneyStates.checkpoint_passport_2,
            5: JourneyStates.checkpoint_leaving_2,
        }

        await state.set_state(state_mapping[checkpoint_index])

        checkpoint = checkpoints[checkpoint_index]
        checkpoint_name = CHECKPOINT_NAMES.get(checkpoint["name"], checkpoint["name"])
        keyboard = create_checkpoint_keyboard()

        await message.answer(
            f"✅ Таймзона изменена: {message.text}\n\n"
            f"📍 Контрольная точка {checkpoint_index + 1}/6\n{checkpoint_name}\n\n"
            f"⏰ Введите время (ЧЧ:ММ) или нажмите '⏰ Сейчас':",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "❌ Пожалуйста, выберите таймзону из предложенных вариантов."
        )


@router.message(F.text == "🌍 Сменить таймзону")
async def cmd_change_timezone(message: Message, state: FSMContext):
    """Handle timezone change request."""
    current_state = await state.get_state()

    # Check if user has active journey
    active_journey = await db.get_user_active_journey(message.from_user.id)

    if current_state is None or active_journey is None:
        keyboard = create_main_menu_keyboard(has_active_journey=False)
        await message.answer(
            "У вас нет активной поездки.\n\n"
            "Используйте '🆕 Новая поездка' чтобы начать отслеживание.",
            reply_markup=keyboard
        )
        return

    # Show timezone selection
    await state.set_state(JourneyStates.changing_timezone)
    keyboard = create_timezone_keyboard(include_cancel=False)

    data = await state.get_data()
    current_tz = data.get("user_timezone", "Europe/Minsk")
    tz_display = get_timezone_display(current_tz)

    await message.answer(
        f"🌍 Текущая таймзона: {tz_display}\n\n"
        f"Выберите новую таймзону:",
        reply_markup=keyboard
    )


@router.message(StateFilter(
    JourneyStates.checkpoint_approaching_border,
    JourneyStates.checkpoint_entering_1,
    JourneyStates.checkpoint_passport_1,
    JourneyStates.checkpoint_entering_2,
    JourneyStates.checkpoint_passport_2,
    JourneyStates.checkpoint_leaving_2
))
async def process_checkpoint_time(message: Message, state: FSMContext):
    """Process checkpoint timestamp."""
    data = await state.get_data()

    # Check for timezone change request
    if message.text == "🌍 Сменить таймзону":
        await cmd_change_timezone(message, state)
        return

    # Check if user wants to cancel
    if message.text == "❌ Отменить поездку":
        await cmd_cancel(message, state)
        return

    # Get timezone selected by user
    user_timezone = data.get("user_timezone", "Europe/Minsk")

    try:
        # Get journey to determine reference time
        journey = await db.get_journey(data["journey_id"])
        journey_events = await db.get_journey_events(data["journey_id"])

        # Reference time is last checkpoint or departure
        if journey_events:
            reference_time = parse_db_timestamp(journey_events[-1]["timestamp_utc"])
        else:
            reference_time = parse_db_timestamp(journey["departure_utc"])

        # Parse checkpoint time intelligently (auto-detects next day)
        timestamp_utc = parse_checkpoint_time(
            message.text,
            reference_time,
            user_timezone
        )
    except ValueError:
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ (например, 14:30)")
        return

    # Validate timestamp order and max duration
    journey_events = await db.get_journey_events(data["journey_id"])
    if journey_events:
        last_event_time = parse_db_timestamp(journey_events[-1]["timestamp_utc"])

        if not validate_checkpoint_order(timestamp_utc, last_event_time, max_hours=24):
            # Check what went wrong
            if timestamp_utc < last_event_time:
                await message.answer(
                    "❌ Неверное время: должно быть после предыдущей контрольной точки.\n"
                    "Пожалуйста, введите корректное время."
                )
            else:
                await message.answer(
                    "❌ Неверное время: разница между чекпоинтами не может быть больше 24 часов.\n"
                    "Пожалуйста, введите корректное время."
                )
            return
    else:
        # First checkpoint - validate against departure
        journey = await db.get_journey(data["journey_id"])
        departure_time = parse_db_timestamp(journey["departure_utc"])

        if not validate_checkpoint_order(timestamp_utc, departure_time, max_hours=24):
            if timestamp_utc < departure_time:
                await message.answer(
                    "❌ Неверное время: должно быть после времени отправления.\n"
                    "Пожалуйста, введите корректное время."
                )
            else:
                await message.answer(
                    "❌ Неверное время: разница между отправлением и первым чекпоинтом не может быть больше 24 часов.\n"
                    "Пожалуйста, введите корректное время."
                )
            return

    # Save checkpoint event
    await db.create_journey_event(
        journey_id=data["journey_id"],
        checkpoint_id=data["current_checkpoint_id"],
        timestamp_utc=timestamp_utc,
        source="manual"
    )

    # Move to next checkpoint
    await state.update_data(current_checkpoint_index=data["current_checkpoint_index"] + 1)
    await start_next_checkpoint(message, state)


async def show_journey_summary(message_or_callback, state: FSMContext):
    """Show journey summary and complete it."""
    data = await state.get_data()
    journey_id = data["journey_id"]

    # Get all events
    events = await db.get_journey_events(journey_id)

    # Calculate durations
    summary_text = "✅ Поездка завершена!\n\n📊 Итоги:\n\n"

    for i, event in enumerate(events):
        checkpoint_name = CHECKPOINT_NAMES.get(
            event["checkpoints"]["name"],
            event["checkpoints"]["name"]
        )
        time_str = format_datetime_for_user(
            parse_db_timestamp(event["timestamp_utc"])
        )
        summary_text += f"{i+1}. {checkpoint_name}\n   ⏰ {time_str}\n"

        if i > 0:
            prev_time = parse_db_timestamp(events[i-1]["timestamp_utc"])
            curr_time = parse_db_timestamp(event["timestamp_utc"])
            duration = curr_time - prev_time
            minutes = int(duration.total_seconds() / 60)
            summary_text += f"   ⌛ +{minutes} мин от предыдущей\n"
        summary_text += "\n"

    # Calculate total duration
    if len(events) >= 2:
        start_time = parse_db_timestamp(events[0]["timestamp_utc"])
        end_time = parse_db_timestamp(events[-1]["timestamp_utc"])
        total_duration = end_time - start_time
        total_minutes = int(total_duration.total_seconds() / 60)

        # Format time nicely with hours and minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0:
            time_str = f"{hours} ч {minutes} мин ({total_minutes} мин)"
        else:
            time_str = f"{total_minutes} мин"

        summary_text += f"🏁 Общее время прохождения границы: {time_str}\n"

    # Complete journey
    await db.complete_journey(journey_id)

    thank_you_text = (
        "Спасибо за вклад! 🙏\n\n"
        "Ваши данные помогают другим планировать поездки.\n\n"
        "Используйте меню внизу для навигации."
    )

    keyboard = create_main_menu_keyboard(has_active_journey=False)

    # Handle both Message and CallbackQuery
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(summary_text)
        await message_or_callback.answer(thank_you_text, reply_markup=keyboard)
    else:  # CallbackQuery
        await message_or_callback.bot.send_message(
            message_or_callback.message.chat.id,
            summary_text
        )
        await message_or_callback.bot.send_message(
            message_or_callback.message.chat.id,
            thank_you_text,
            reply_markup=keyboard
        )

    await state.clear()


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отменить поездку")
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel current journey - ask for confirmation."""
    current_state = await state.get_state()

    # Check if there's an active journey in database
    active_journey = await db.get_user_active_journey(message.from_user.id)

    if current_state is None and active_journey is None:
        keyboard = create_main_menu_keyboard(has_active_journey=False)
        await message.answer(
            "Нет активной поездки для отмены.",
            reply_markup=keyboard
        )
        return

    # Ask for confirmation
    keyboard = create_cancel_confirmation_keyboard()
    await message.answer(
        "⚠️ Вы уверены что хотите отменить текущую поездку?\n\n"
        "Все введённые данные будут потеряны.",
        reply_markup=keyboard
    )


# Confirmation handlers for cancel
@router.callback_query(F.data == "confirm_cancel_yes")
async def confirm_cancel_yes(callback: CallbackQuery, state: FSMContext):
    """User confirmed cancellation."""
    await callback.answer()

    # Mark journey as cancelled in database
    active_journey = await db.get_user_active_journey(callback.from_user.id)
    if active_journey:
        try:
            # Try to use cancel_journey if cancelled field exists
            await db.cancel_journey(active_journey["id"])
            print(f"✅ Journey {active_journey['id']} marked as cancelled")
        except Exception as e:
            # Fallback to complete_journey if cancelled field doesn't exist yet
            print(f"⚠️ cancel_journey failed, using complete_journey: {e}")
            await db.complete_journey(active_journey["id"])
            print(f"✅ Journey {active_journey['id']} marked as completed")

    # Clear FSM state
    await state.clear()

    keyboard = create_main_menu_keyboard(has_active_journey=False)

    # Delete confirmation message
    try:
        await callback.message.delete()
    except Exception:
        pass

    # Send new message with keyboard
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text="❌ Поездка отменена.\n\n"
             "Используйте '🆕 Новая поездка' чтобы начать отслеживание.",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "confirm_cancel_no")
async def confirm_cancel_no(callback: CallbackQuery, state: FSMContext):
    """User declined cancellation."""
    await callback.answer("Продолжаем поездку")

    keyboard = create_checkpoint_keyboard()
    await callback.message.edit_text(
        "✅ Продолжаем отслеживание поездки.\n\n"
        "Используйте '⏰ Ввести время' или '⏰ Сейчас' для ввода времени контрольной точки."
    )
    await callback.message.answer(
        "Меню:",
        reply_markup=keyboard
    )


@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message, state: FSMContext):
    """Show latest border crossing statistics."""
    journeys = await db.get_latest_border_stats(limit=5)

    # Check if user has active journey for menu
    active_journey = await db.get_user_active_journey(message.from_user.id)
    keyboard = create_main_menu_keyboard(has_active_journey=active_journey is not None)

    if not journeys:
        await message.answer(
            "📊 Данных пока нет. Будьте первым, кто внесёт свой вклад!",
            reply_markup=keyboard
        )
        return

    stats_text = "📊 Последние пересечения границы:\n\n"

    for journey in journeys:
        carrier_name = journey.get("carriers", {}).get("name", "Неизвестно")
        events = journey.get("journey_events", [])

        if len(events) >= 2:
            start_time = parse_db_timestamp(events[0]["timestamp_utc"])
            end_time = parse_db_timestamp(events[-1]["timestamp_utc"])
            duration = end_time - start_time
            minutes = int(duration.total_seconds() / 60)

            # Format time nicely with hours and minutes
            hours = minutes // 60
            mins = minutes % 60

            if hours > 0:
                time_str = f"{hours} ч {mins} мин"
            else:
                time_str = f"{minutes} мин"

            # Convert to Minsk timezone for display
            date_str = format_datetime_for_user(end_time, "Europe/Minsk")
            stats_text += f"🚌 {carrier_name}\n"
            stats_text += f"📅 {date_str}\n"
            stats_text += f"⌛ {time_str}\n\n"

    await message.answer(stats_text, reply_markup=keyboard)


# Handler for "Ввести время" button
@router.message(F.text == "⏰ Ввести время")
async def cmd_enter_time(message: Message, state: FSMContext):
    """Handle 'Enter time' button press."""
    current_state = await state.get_state()

    # Get active journey
    active_journey = await db.get_user_active_journey(message.from_user.id)

    if current_state is None or active_journey is None:
        keyboard = create_main_menu_keyboard(has_active_journey=False)
        await message.answer(
            "У вас нет активной поездки.\n\n"
            "Используйте '🆕 Новая поездка' чтобы начать отслеживание.",
            reply_markup=keyboard
        )
        return

    # Get current checkpoint info
    data = await state.get_data()
    checkpoint_index = data.get("current_checkpoint_index", 0)
    checkpoints = await db.get_mandatory_checkpoints()

    if checkpoint_index >= len(checkpoints):
        await message.answer(
            "Все контрольные точки уже пройдены!",
            reply_markup=create_main_menu_keyboard(has_active_journey=False)
        )
        return

    checkpoint = checkpoints[checkpoint_index]
    checkpoint_name = CHECKPOINT_NAMES.get(checkpoint["name"], checkpoint["name"])

    # Get current timezone
    current_tz = data.get("user_timezone", "Europe/Minsk")
    tz_display = get_timezone_display(current_tz)

    keyboard = create_checkpoint_keyboard()
    await message.answer(
        f"📍 Контрольная точка {checkpoint_index + 1}/6\n"
        f"{checkpoint_name}\n\n"
        f"🌍 Таймзона: {tz_display}\n"
        f"⏰ Введите время (ЧЧ:ММ) или нажмите '⏰ Сейчас':",
        reply_markup=keyboard
    )

