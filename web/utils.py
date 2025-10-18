import logging
import time
from datetime import datetime, timezone


logger = logging.getLogger(__package__)


def get_timer_name(job) -> str:
    return job['name'].replace(' ', '_') + ".timer"


def get_service_name(job) -> str:
    return job['name'].replace(' ', '_') + ".service"


def calculate_duration_to_now(systemd_date: str, full: bool=True) -> str:
    logger.debug("Will convert systemd date: >>" + systemd_date +"<<")
    if not systemd_date:
        return ""

    to_time = time.time()
    from_time = convert_systemd_date(systemd_date)

    duration_in_seconds = int(to_time - from_time)
    minutes, seconds = divmod(duration_in_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    months, days = divmod(days, 30)
    years, months = divmod(months, 12)

    parts = [
        (years, "y"),
        (months, "M"),
        (days, "d"),
        (hours, "h"),
        (minutes, "m"),
        (seconds, "s"),
    ]
    if full:
        return ''.join(f"{value}{label}"
            for value, label in parts
            if value or (label == "s"))
    else:
        # find index of first nonzero part
        first_idx = next((i for i, (v, _) in enumerate(parts) if v > 0), None)

        if first_idx is None:
            return "0s"

        display_parts = parts[first_idx:first_idx + 2]
        return ''.join(f"{value}{label}" for value, label in display_parts)


def convert_systemd_date(systemd_date: str) -> float:
    dt = datetime.strptime(systemd_date, "%a %Y-%m-%d %H:%M:%S %Z")

    # Ensure it's treated as UTC
    dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()
