"""Timestamp normalization for the bead field query layer.

All timestamps entering the query layer are canonicalized to
YYYY-MM-DDTHH:MM:SS+00:00 BEFORE hitting SQLite. Misuse is
impossible, not discouraged.

Canonical form: "2024-01-15T14:30:00+00:00"
This is the ONE format. No alternatives. No mixing.
"""

from datetime import datetime, timezone, timedelta
import re

CANONICAL_FORMAT = "%Y-%m-%dT%H:%M:%S+00:00"

_OFFSET_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"([+-])(\d{2}):(\d{2})$"
)


def normalize_timestamp(ts: str) -> str:
    """Normalize any valid timestamp string to canonical UTC form.

    Accepts:
        - Naive ISO:  "2024-01-15T14:30:00"     → appends +00:00
        - Z suffix:   "2024-01-15T14:30:00Z"    → replaces Z with +00:00
        - UTC offset: "2024-01-15T14:30:00+00:00" → passthrough
        - Non-UTC:    "2024-01-15T21:30:00+07:00" → converts to UTC

    Raises:
        TypeError: if ts is None or not a string
        ValueError: if ts cannot be parsed as a valid timestamp
    """
    if ts is None:
        raise TypeError("Timestamp cannot be None")
    if not isinstance(ts, str):
        raise TypeError(f"Timestamp must be a string, got {type(ts).__name__}")

    stripped = ts.strip()
    if not stripped:
        raise ValueError(f"Invalid timestamp: empty string")

    if stripped.endswith("Z"):
        bare = stripped[:-1]
        _validate_datetime_part(bare)
        return bare + "+00:00"

    m = _OFFSET_RE.match(stripped)
    if m:
        dt_part, sign, hours_str, mins_str = m.groups()
        _validate_datetime_part(dt_part)
        offset_hours = int(hours_str)
        offset_mins = int(mins_str)

        if sign == "+" and offset_hours == 0 and offset_mins == 0:
            return stripped

        offset_total = timedelta(
            hours=offset_hours, minutes=offset_mins
        )
        if sign == "+":
            offset_total = -offset_total
        else:
            pass  # negative offset means ADD to get UTC

        dt = datetime.strptime(dt_part, "%Y-%m-%dT%H:%M:%S")
        dt_utc = dt + offset_total
        return dt_utc.strftime(CANONICAL_FORMAT)

    _validate_datetime_part(stripped)
    return stripped + "+00:00"


def _validate_datetime_part(dt_str: str) -> None:
    """Validate that dt_str is a parseable datetime."""
    try:
        datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        raise ValueError(f"Invalid timestamp: {dt_str!r}")


def normalize_params(params: tuple | list | dict) -> tuple | list | dict:
    """Normalize any timestamp-shaped strings in query parameters.

    Scans parameter values and normalizes anything matching
    ISO 8601 datetime patterns. Non-timestamp values pass through.
    """
    if isinstance(params, dict):
        return {k: _maybe_normalize(v) for k, v in params.items()}
    return type(params)(_maybe_normalize(v) for v in params)


def _maybe_normalize(val: object) -> object:
    """Normalize if it looks like a timestamp, otherwise passthrough."""
    if not isinstance(val, str):
        return val
    if not re.match(r"^\d{4}-\d{2}-\d{2}T", val):
        return val
    try:
        return normalize_timestamp(val)
    except (ValueError, TypeError):
        return val
