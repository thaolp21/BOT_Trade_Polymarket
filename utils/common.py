from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def r2(val, ndigits: int = 2):
    """Round a numeric value safely to ndigits. If it fails, return original.
    Accepts int/float-like values; returns rounded float or original.
    """
    try:
        return round(val, ndigits)
    except Exception:
        return val


# --- DateTime Utility Functions ---

# Timezone constants
GMT7_TZ = 'Asia/Bangkok'
ET_TZ = 'US/Eastern'

def timestamp_to_timezone(ts: int, target_tz: str, format_str: str) -> str:
    """Convert Unix timestamp to formatted string in target timezone."""
    if not ts:
        return ''
    utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    target_zone = ZoneInfo(target_tz)
    return utc_dt.astimezone(target_zone).strftime(format_str)

def to_et_time(ts: int) -> str:
    """Convert timestamp to Eastern Time format."""
    return timestamp_to_timezone(ts, ET_TZ, '%Y-%m-%d %I:%M %p')

def to_gmt7_date(ts: int) -> str:
    """Convert timestamp to GMT+7 date format (dd.MM.yyyy)."""
    return timestamp_to_timezone(ts, GMT7_TZ, '%d.%m.%Y')

def to_gmt7_datetime(ts: int) -> str:
    """Convert timestamp to GMT+7 datetime format."""
    return timestamp_to_timezone(ts, GMT7_TZ, '%Y-%m-%d %H:%M:%S')

def extract_time_part(ts: int) -> str:
    """Extract time part (HH:MM AM/PM) from timestamp in ET."""
    if not ts:
        return ''
    full_time = to_et_time(ts)
    parts = full_time.split(' ')
    return f"{parts[1]} {parts[2]}" if len(parts) >= 3 else ''
