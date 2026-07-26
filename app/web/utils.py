import logging
import time
import os


logger = logging.getLogger(__package__)

_fqdn_or_ip = None


def calculate_duration_to_now(epoch: float, full: bool=True) -> str:
    if not epoch or epoch == "":
        return ""
    return calculate_duration_from_to(epoch, time.time(), full)


def calculate_duration_from_now(epoch: float, full: bool=True) -> str:
    if not epoch or epoch == "":
        return ""
    return calculate_duration_from_to(time.time(), epoch, full)


def calculate_duration_from_to(fromm:float, to: float, full: bool=True) -> str:
    if not fromm or not to:
        return ""

    if fromm > to:
        return "-" + calculate_duration_from_to(to, fromm, full)

    duration_in_seconds = int(to - fromm)
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

    #We always strip leading 0 entries
    first_idx = next((i for i, (v, _) in enumerate(parts) if v > 0), None)
    if first_idx is None:
            return "0s"

    #Full mode: show trailing 0 entries. Non-full: only show the 2 most-left (most important) non 0 entries
    display_parts = parts[first_idx:] if full else parts[first_idx:first_idx + 2]
    return ''.join(f"{value}{label}" for value, label in display_parts)



def detect_fqdn_or_ip() -> str:
    global _fqdn_or_ip
    if _fqdn_or_ip:
        return _fqdn_or_ip

    fqdn = os.popen('hostname -f').read().strip()
    if not fqdn or '.' not in fqdn:
        result = os.popen('ip a s dev eth0').read()
        for line in result.splitlines():
            line = line.strip()
            if line.startswith('inet '):
                fqdn = line.split()[1].split('/')[0]
                break

    _fqdn_or_ip = fqdn or "localhost"
    return _fqdn_or_ip


