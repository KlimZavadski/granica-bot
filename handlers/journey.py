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
    format_datetime_for_user,
    validate_checkpoint_order,
    parse_db_timestamp,
    create_calendar,
    get_next_month,
    get_prev_month,
    create_time_keyboard
)

router = Router()

# Checkpoint display names
CHECKPOINT_NAMES = {
    "approaching_border": "🚌 Подъезжаем к границе",
    "entering_checkpoint_1": "🛂 Въезд на КПП #1",
    "invited_passport_control_1": "👮 Приглашены на паспортный контроль #1",
    "leaving_checkpoint_1": "🚪 Покидаем КПП #1 (нейтральная зона)",
    "entering_checkpoint_2": "🛂 Въезд на КПП #2",
    "invited_passport_control_2": "👮 Приглашены на паспортный контроль #2",
    "leaving_checkpoint_2": "✅ Покидаем КПП #2 (выезд с границы)"
}


def create_carrier_keyboard(carriers: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """Create keyboard with carrier options."""
    buttons = [[KeyboardButton(text=carrier["name"])] for carrier in carriers]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def create_now_skip_keyboard(show_skip: bool = False) -> ReplyKeyboardMarkup:
    """Create keyboard with 'Now' and optionally 'Skip' options."""
    buttons = [[KeyboardButton(text="⏰ Сейчас")]]
    if show_skip:
        buttons.append([KeyboardButton(text="⏭ Пропустить")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command - show welcome and instructions."""
    welcome_text = (
        "👋 Добро пожаловать в Granica Bot!\n\n"
        "Этот бот помогает отслеживать время прохождения границы между Беларусью и Польшей/Литвой.\n\n"
        "📝 Как это работает:\n"
        "1. Выберите перевозчика\n"
        "2. Укажите время отправления\n"
        "3. Отмечайте контрольные точки по мере прохождения\n"
        "4. Просматривайте статистику и помогайте другим планировать поездки\n\n"
        "⏰ Все время автоматически обрабатывается в UTC\n\n"
        "Используйте /new чтобы начать отслеживание поездки\n"
        "Используйте /stats чтобы посмотреть последние данные о границе\n"
        "Используйте /cancel чтобы отменить текущую поездку"
    )
    await message.answer(welcome_text)


@router.message(Command("new"))
async def cmd_new_journey(message: Message, state: FSMContext):
    """Start a new journey."""
    # Check if user has an active journey
    active_journey = await db.get_user_active_journey(message.from_user.id)
    if active_journey:
        await message.answer(
            "⚠️ У вас уже есть активная поездка. Используйте /cancel чтобы отменить её.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Get carriers from database
    carriers = await db.get_carriers()
    keyboard = create_carrier_keyboard(carriers)

    await state.set_state(JourneyStates.choosing_carrier)
    await message.answer(
        "🚌 Выберите перевозчика:",
        reply_markup=keyboard
    )


@router.message(JourneyStates.choosing_carrier)
async def process_carrier_choice(message: Message, state: FSMContext):
    """Process carrier selection."""
    carriers = await db.get_carriers()
    carrier = next((c for c in carriers if c["name"] == message.text), None)

    if not carrier:
        await message.answer("❌ Неверный перевозчик. Пожалуйста, выберите из списка.")
        return

    await state.update_data(carrier_id=carrier["id"], carrier_name=carrier["name"])
    await state.set_state(JourneyStates.entering_departure_date)

    # First, remove the reply keyboard
    await message.answer(
        f"✅ Выбран перевозчик: {carrier['name']}",
        reply_markup=ReplyKeyboardRemove()
    )

    # Then show calendar for date selection
    calendar = create_calendar()
    await message.answer(
        "📅 Выберите дату отправления:",
        reply_markup=calendar
    )


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

        try:
            # Edit the calendar message to show selected date and time picker
            print(f"📝 Trying to edit message...")
            await callback.message.edit_text(
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
            await callback.bot.send_message(
                callback.message.chat.id,
                f"✅ Дата выбрана: {day:02d}.{month:02d}.{year}\n\n"
                "🕐 Выберите время отправления:",
                reply_markup=time_keyboard
            )
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
        # Switch to manual time entry
        try:
            await callback.message.edit_text(
                "✏️ Введите время отправления вручную (ЧЧ:ММ):\n"
                "Пример: 14:30"
            )
        except Exception:
            await callback.message.delete()
            await callback.bot.send_message(
                callback.message.chat.id,
                "✏️ Введите время отправления вручную (ЧЧ:ММ):\n"
                "Пример: 14:30"
            )
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

    # Edit message to show journey created
    try:
        await callback.message.edit_text(
            f"✅ Поездка создана!\n"
            f"🚌 Перевозчик: {data['carrier_name']}\n"
            f"📅 Отправление: {data['departure_date']} {time_str}\n\n"
            f"Теперь отмечайте контрольные точки по мере прохождения.\n"
            f"Нажмите '⏰ Сейчас' чтобы использовать текущее время, или введите время вручную (ЧЧ:ММ)."
        )
    except Exception as e:
        print(f"Error editing message: {e}")
        await callback.message.delete()
        await callback.bot.send_message(
            callback.message.chat.id,
            f"✅ Поездка создана!\n"
            f"🚌 Перевозчик: {data['carrier_name']}\n"
            f"📅 Отправление: {data['departure_date']} {time_str}\n\n"
            f"Теперь отмечайте контрольные точки по мере прохождения.\n"
            f"Нажмите '⏰ Сейчас' чтобы использовать текущее время, или введите время вручную (ЧЧ:ММ)."
        )

    # Move to first checkpoint
    await start_next_checkpoint(callback, state)


@router.message(JourneyStates.entering_departure_time)
async def process_departure_time(message: Message, state: FSMContext):
    """Process departure time (manual text input)."""
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

        await message.answer(
            f"✅ Поездка создана!\n"
            f"🚌 Перевозчик: {data['carrier_name']}\n"
            f"📅 Отправление: {data['departure_date']} {message.text}\n\n"
            f"Теперь отмечайте контрольные точки по мере прохождения.\n"
            f"Нажмите '⏰ Сейчас' чтобы использовать текущее время, или введите время вручную (ЧЧ:ММ)."
        )

        # Move to first checkpoint
        await start_next_checkpoint(message, state)

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
        3: JourneyStates.checkpoint_leaving_1,
        4: JourneyStates.checkpoint_entering_2,
        5: JourneyStates.checkpoint_passport_2,
        6: JourneyStates.checkpoint_leaving_2,
    }

    await state.set_state(state_mapping[checkpoint_index])
    await state.update_data(current_checkpoint_id=checkpoint["id"])

    keyboard = create_now_skip_keyboard(show_skip=False)

    # Handle both Message and CallbackQuery
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(
            f"📍 Контрольная точка {checkpoint_index + 1}/7\n{checkpoint_name}\n\n"
            f"Введите время (ЧЧ:ММ) или нажмите '⏰ Сейчас':",
            reply_markup=keyboard
        )
    else:  # CallbackQuery
        await message_or_callback.bot.send_message(
            message_or_callback.message.chat.id,
            f"📍 Контрольная точка {checkpoint_index + 1}/7\n{checkpoint_name}\n\n"
            f"Введите время (ЧЧ:ММ) или нажмите '⏰ Сейчас':",
            reply_markup=keyboard
        )


@router.message(StateFilter(
    JourneyStates.checkpoint_approaching_border,
    JourneyStates.checkpoint_entering_1,
    JourneyStates.checkpoint_passport_1,
    JourneyStates.checkpoint_leaving_1,
    JourneyStates.checkpoint_entering_2,
    JourneyStates.checkpoint_passport_2,
    JourneyStates.checkpoint_leaving_2
))
async def process_checkpoint_time(message: Message, state: FSMContext):
    """Process checkpoint timestamp."""
    data = await state.get_data()

    # Determine timestamp
    if message.text == "⏰ Сейчас":
        timestamp_utc = now_utc()
    else:
        try:
            # Parse time with today's date
            timestamp_utc = parse_user_datetime(
                data["departure_date"],
                message.text,
                "Europe/Minsk"
            )
        except ValueError:
            await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ или нажмите '⏰ Сейчас'")
            return

    # Validate timestamp order
    journey_events = await db.get_journey_events(data["journey_id"])
    if journey_events:
        last_event_time = parse_db_timestamp(journey_events[-1]["timestamp_utc"])

        if not validate_checkpoint_order(timestamp_utc, last_event_time):
            await message.answer(
                "❌ Неверное время: должно быть после предыдущей контрольной точки.\n"
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
        summary_text += f"🏁 Общее время прохождения границы: {total_minutes} минут\n"

    # Complete journey
    await db.complete_journey(journey_id)

    thank_you_text = (
        "Спасибо за вклад! 🙏\n\n"
        "Ваши данные помогают другим планировать поездки.\n\n"
        "Используйте /new чтобы отследить следующую поездку\n"
        "Используйте /stats чтобы посмотреть статистику"
    )

    # Handle both Message and CallbackQuery
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(summary_text, reply_markup=ReplyKeyboardRemove())
        await message_or_callback.answer(thank_you_text)
    else:  # CallbackQuery
        await message_or_callback.bot.send_message(
            message_or_callback.message.chat.id,
            summary_text
        )
        await message_or_callback.bot.send_message(
            message_or_callback.message.chat.id,
            thank_you_text
        )

    await state.clear()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel current journey."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной поездки для отмены.")
        return

    await state.clear()
    await message.answer(
        "❌ Поездка отменена.\n\nИспользуйте /new чтобы начать новую поездку.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show latest border crossing statistics."""
    journeys = await db.get_latest_border_stats(limit=5)

    if not journeys:
        await message.answer("📊 Данных пока нет. Будьте первым, кто внесёт свой вклад!")
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

            date_str = start_time.strftime("%Y-%m-%d %H:%M")
            stats_text += f"🚌 {carrier_name}\n"
            stats_text += f"📅 {date_str}\n"
            stats_text += f"⌛ {minutes} минут\n\n"

    await message.answer(stats_text)

