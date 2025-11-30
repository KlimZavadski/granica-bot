"""Timezone handling utilities."""
from datetime import datetime, timezone
import pytz
from typing import Optional


def to_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to UTC.
    If naive, assumes it's already UTC.
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)


def from_utc_to_timezone(dt: datetime, tz_name: str) -> datetime:
    """Convert UTC datetime to specific timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    tz = pytz.timezone(tz_name)
    return dt.astimezone(tz)


def now_utc() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def parse_user_datetime(date_str: str, time_str: str, user_tz: str = "Europe/Minsk") -> datetime:
    """
    Parse user input date and time, convert to UTC.

    Args:
        date_str: Date in format YYYY-MM-DD
        time_str: Time in format HH:MM
        user_tz: User's timezone (default: Europe/Minsk for Belarus)

    Returns:
        UTC datetime
    """
    tz = pytz.timezone(user_tz)
    dt_str = f"{date_str} {time_str}"
    naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    local_dt = tz.localize(naive_dt)
    return local_dt.astimezone(timezone.utc)


def format_datetime_for_user(dt: datetime, tz_name: str = "Europe/Minsk") -> str:
    """Format UTC datetime for display to user in their timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = from_utc_to_timezone(dt, tz_name)

    # Calculate UTC offset
    offset = local_dt.utcoffset()
    if offset is not None:
        total_seconds = int(offset.total_seconds())
        hours = total_seconds // 3600
        utc_offset = f"UTC{hours:+d}"
    else:
        utc_offset = "UTC"

    return local_dt.strftime(f"%Y-%m-%d %H:%M ({utc_offset})")


def parse_db_timestamp(timestamp_value) -> datetime:
    """
    Parse timestamp from database (can be string or datetime object).
    Always returns timezone-aware datetime in UTC.

    Args:
        timestamp_value: Timestamp from database (string or datetime)

    Returns:
        Timezone-aware datetime in UTC
    """
    if isinstance(timestamp_value, str):
        # Remove 'Z' and add UTC timezone
        dt = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
    else:
        dt = timestamp_value

    # Ensure it's UTC
    return to_utc(dt)


def parse_checkpoint_time(
    time_str: str,
    reference_datetime: datetime,
    user_tz: str = "Europe/Minsk"
) -> datetime:
    """
    Parse checkpoint time intelligently determining the correct date.

    If the time is earlier than reference time, assumes it's next day.
    This handles cases like: departure 20:00 on Nov 27, checkpoint 01:43 → Nov 28 01:43

    Args:
        time_str: Time in format HH:MM
        reference_datetime: Reference datetime (departure or previous checkpoint) in UTC
        user_tz: User's timezone (default: Europe/Minsk for Belarus)

    Returns:
        UTC datetime with correct date
    """
    tz = pytz.timezone(user_tz)

    # Convert reference to user timezone to get the correct date
    ref_local = reference_datetime.astimezone(tz)

    # Parse time with reference date
    time_obj = datetime.strptime(time_str, "%H:%M").time()
    candidate_dt = datetime.combine(ref_local.date(), time_obj)
    candidate_dt = tz.localize(candidate_dt)

    # If candidate is before reference, it's next day
    if candidate_dt <= ref_local:
        from datetime import timedelta
        next_day = ref_local.date() + timedelta(days=1)
        candidate_dt = datetime.combine(next_day, time_obj)
        candidate_dt = tz.localize(candidate_dt)

    # Convert to UTC
    return candidate_dt.astimezone(timezone.utc)


def validate_checkpoint_order(
    new_timestamp: datetime,
    previous_timestamp: Optional[datetime],
    max_hours: int = 24
) -> bool:
    """
    Validate that checkpoint timestamps are in order and within reasonable time.

    Args:
        new_timestamp: New checkpoint timestamp
        previous_timestamp: Previous checkpoint timestamp (or None if first)
        max_hours: Maximum hours between checkpoints (default: 24)

    Returns:
        True if valid, False otherwise
    """
    if previous_timestamp is None:
        return True

    # Normalize both timestamps to UTC for comparison
    new_utc = to_utc(new_timestamp)
    prev_utc = to_utc(previous_timestamp)

    # Must be after previous
    if new_utc < prev_utc:
        return False

    # Must not be more than max_hours apart
    from datetime import timedelta
    max_delta = timedelta(hours=max_hours)
    if (new_utc - prev_utc) > max_delta:
        return False

    return True

