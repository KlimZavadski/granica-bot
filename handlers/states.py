"""FSM states for journey tracking."""
from aiogram.fsm.state import State, StatesGroup


class JourneyStates(StatesGroup):
    """States for tracking a border crossing journey."""

    # Initial setup
    choosing_carrier = State()
    entering_departure_date = State()
    entering_departure_time = State()
    choosing_initial_timezone = State()

    # Timezone management
    changing_timezone = State()

    # Mandatory checkpoints (in order)
    checkpoint_approaching_border = State()
    checkpoint_entering_1 = State()
    checkpoint_passport_1 = State()
    checkpoint_leaving_1 = State()
    checkpoint_entering_2 = State()
    checkpoint_passport_2 = State()
    checkpoint_leaving_2 = State()

    # Optional checkpoints
    add_optional_checkpoint = State()

    # Summary
    journey_summary = State()

