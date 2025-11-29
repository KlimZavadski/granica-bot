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
    return local_dt.strftime("%Y-%m-%d %H:%M %Z")


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


def validate_checkpoint_order(
    new_timestamp: datetime,
    previous_timestamp: Optional[datetime]
) -> bool:
    """
    Validate that checkpoint timestamps are in order.

    Args:
        new_timestamp: New checkpoint timestamp
        previous_timestamp: Previous checkpoint timestamp (or None if first)

    Returns:
        True if valid, False otherwise
    """
    if previous_timestamp is None:
        return True

    # Normalize both timestamps to UTC for comparison
    new_utc = to_utc(new_timestamp)
    prev_utc = to_utc(previous_timestamp)

    return new_utc >= prev_utc

