"""Journey tracking handlers."""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime
from typing import List, Dict, Any

from .states import JourneyStates
from database import db
from utils import now_utc, parse_user_datetime, format_datetime_for_user, validate_checkpoint_order

router = Router()

# Checkpoint display names
CHECKPOINT_NAMES = {
    "approaching_border": "🚌 Approaching the border",
    "entering_checkpoint_1": "🛂 Entering checkpoint #1",
    "invited_passport_control_1": "👮 Invited to passport control #1",
    "leaving_checkpoint_1": "🚪 Leaving checkpoint #1 (neutral zone)",
    "entering_checkpoint_2": "🛂 Entering checkpoint #2",
    "invited_passport_control_2": "👮 Invited to passport control #2",
    "leaving_checkpoint_2": "✅ Leaving checkpoint #2 (border exit)"
}


def create_carrier_keyboard(carriers: List[Dict[str, Any]]) -> ReplyKeyboardMarkup:
    """Create keyboard with carrier options."""
    buttons = [[KeyboardButton(text=carrier["name"])] for carrier in carriers]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def create_now_skip_keyboard(show_skip: bool = False) -> ReplyKeyboardMarkup:
    """Create keyboard with 'Now' and optionally 'Skip' options."""
    buttons = [[KeyboardButton(text="⏰ Now")]]
    if show_skip:
        buttons.append([KeyboardButton(text="⏭ Skip")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Start command - show welcome and instructions."""
    welcome_text = (
        "👋 Welcome to Granica Bot!\n\n"
        "This bot helps track border crossing times between Belarus and Poland/Lithuania.\n\n"
        "📝 How it works:\n"
        "1. Select your bus carrier\n"
        "2. Enter departure time\n"
        "3. Record checkpoint timestamps as you pass them\n"
        "4. View statistics and help others plan their trips\n\n"
        "⏰ All times are automatically handled in UTC\n\n"
        "Use /new to start tracking a new journey\n"
        "Use /stats to see latest border crossing data\n"
        "Use /cancel to cancel current journey"
    )
    await message.answer(welcome_text)


@router.message(Command("new"))
async def cmd_new_journey(message: Message, state: FSMContext):
    """Start a new journey."""
    # Check if user has an active journey
    active_journey = await db.get_user_active_journey(message.from_user.id)
    if active_journey:
        await message.answer(
            "⚠️ You already have an active journey. Use /cancel to cancel it first.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Get carriers from database
    carriers = await db.get_carriers()
    keyboard = create_carrier_keyboard(carriers)

    await state.set_state(JourneyStates.choosing_carrier)
    await message.answer(
        "🚌 Choose your bus carrier:",
        reply_markup=keyboard
    )


@router.message(JourneyStates.choosing_carrier)
async def process_carrier_choice(message: Message, state: FSMContext):
    """Process carrier selection."""
    carriers = await db.get_carriers()
    carrier = next((c for c in carriers if c["name"] == message.text), None)

    if not carrier:
        await message.answer("❌ Invalid carrier. Please choose from the list.")
        return

    await state.update_data(carrier_id=carrier["id"], carrier_name=carrier["name"])
    await state.set_state(JourneyStates.entering_departure_date)

    await message.answer(
        "📅 Enter departure date (YYYY-MM-DD):\n"
        "Example: 2024-11-29",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(JourneyStates.entering_departure_date)
async def process_departure_date(message: Message, state: FSMContext):
    """Process departure date."""
    try:
        datetime.strptime(message.text, "%Y-%m-%d")
        await state.update_data(departure_date=message.text)
        await state.set_state(JourneyStates.entering_departure_time)

        await message.answer(
            "🕐 Enter departure time (HH:MM):\n"
            "Example: 14:30",
            reply_markup=ReplyKeyboardRemove()
        )
    except ValueError:
        await message.answer("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2024-11-29)")


@router.message(JourneyStates.entering_departure_time)
async def process_departure_time(message: Message, state: FSMContext):
    """Process departure time and create journey."""
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
            f"✅ Journey created!\n"
            f"🚌 Carrier: {data['carrier_name']}\n"
            f"📅 Departure: {data['departure_date']} {message.text}\n\n"
            f"Now, let's record checkpoint timestamps as you pass them.\n"
            f"Press '⏰ Now' to use current time, or enter time manually (HH:MM).",
            reply_markup=ReplyKeyboardRemove()
        )

        # Move to first checkpoint
        await start_next_checkpoint(message, state)

    except ValueError:
        await message.answer("❌ Invalid time format. Please use HH:MM (e.g., 14:30)")


async def start_next_checkpoint(message: Message, state: FSMContext):
    """Start recording next checkpoint."""
    data = await state.get_data()
    checkpoint_index = data["current_checkpoint_index"]
    checkpoints = await db.get_mandatory_checkpoints()

    if checkpoint_index >= len(checkpoints):
        # All mandatory checkpoints done
        await show_journey_summary(message, state)
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
    await message.answer(
        f"📍 Checkpoint {checkpoint_index + 1}/7\n{checkpoint_name}\n\n"
        f"Enter time (HH:MM) or press '⏰ Now':",
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
    if message.text == "⏰ Now":
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
            await message.answer("❌ Invalid time format. Please use HH:MM or press '⏰ Now'")
            return

    # Validate timestamp order
    journey_events = await db.get_journey_events(data["journey_id"])
    if journey_events:
        last_event_time = datetime.fromisoformat(journey_events[-1]["timestamp_utc"].replace("Z", "+00:00"))
        if not validate_checkpoint_order(timestamp_utc, last_event_time):
            await message.answer(
                "❌ Invalid time: must be after previous checkpoint.\n"
                "Please enter a valid time."
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


async def show_journey_summary(message: Message, state: FSMContext):
    """Show journey summary and complete it."""
    data = await state.get_data()
    journey_id = data["journey_id"]

    # Get all events
    events = await db.get_journey_events(journey_id)

    # Calculate durations
    summary_text = "✅ Journey completed!\n\n📊 Summary:\n\n"

    for i, event in enumerate(events):
        checkpoint_name = CHECKPOINT_NAMES.get(
            event["checkpoints"]["name"],
            event["checkpoints"]["name"]
        )
        time_str = format_datetime_for_user(
            datetime.fromisoformat(event["timestamp_utc"].replace("Z", "+00:00"))
        )
        summary_text += f"{i+1}. {checkpoint_name}\n   ⏰ {time_str}\n"

        if i > 0:
            prev_time = datetime.fromisoformat(events[i-1]["timestamp_utc"].replace("Z", "+00:00"))
            curr_time = datetime.fromisoformat(event["timestamp_utc"].replace("Z", "+00:00"))
            duration = curr_time - prev_time
            minutes = int(duration.total_seconds() / 60)
            summary_text += f"   ⌛ +{minutes} min from previous\n"
        summary_text += "\n"

    # Calculate total duration
    if len(events) >= 2:
        start_time = datetime.fromisoformat(events[0]["timestamp_utc"].replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(events[-1]["timestamp_utc"].replace("Z", "+00:00"))
        total_duration = end_time - start_time
        total_minutes = int(total_duration.total_seconds() / 60)
        summary_text += f"🏁 Total border crossing time: {total_minutes} minutes\n"

    # Complete journey
    await db.complete_journey(journey_id)

    await message.answer(summary_text, reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "Thank you for contributing! 🙏\n\n"
        "Your data helps others plan their trips.\n\n"
        "Use /new to track another journey\n"
        "Use /stats to see latest statistics"
    )

    await state.clear()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel current journey."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("No active journey to cancel.")
        return

    await state.clear()
    await message.answer(
        "❌ Journey cancelled.\n\nUse /new to start a new journey.",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show latest border crossing statistics."""
    journeys = await db.get_latest_border_stats(limit=5)

    if not journeys:
        await message.answer("📊 No data available yet. Be the first to contribute!")
        return

    stats_text = "📊 Latest border crossings:\n\n"

    for journey in journeys:
        carrier_name = journey.get("carriers", {}).get("name", "Unknown")
        events = journey.get("journey_events", [])

        if len(events) >= 2:
            start_time = datetime.fromisoformat(events[0]["timestamp_utc"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(events[-1]["timestamp_utc"].replace("Z", "+00:00"))
            duration = end_time - start_time
            minutes = int(duration.total_seconds() / 60)

            date_str = start_time.strftime("%Y-%m-%d %H:%M")
            stats_text += f"🚌 {carrier_name}\n"
            stats_text += f"📅 {date_str}\n"
            stats_text += f"⌛ {minutes} minutes\n\n"

    await message.answer(stats_text)

