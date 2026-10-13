import time

def format_date(date) -> str:
    return date.strftime('%Y-%m-%d %H:%M:%S')



def format_duration(duration_in_seconds: float, full: bool=True) -> str:
    if duration_in_seconds is None or not isinstance(duration_in_seconds, (int, float)):
        return None
    return calculate_duration_from_to(0.0, duration_in_seconds, full)



def calculate_duration_to_now(epoch: float, full: bool=True) -> str:
    if epoch is None or not isinstance(epoch, (int, float)):
        return None
    return calculate_duration_from_to(epoch, time.time(), full)



def calculate_duration_from_now(epoch: float, full: bool=True) -> str:
    if epoch is None or not isinstance(epoch, (int, float)):
        return None
    return calculate_duration_from_to(time.time(), epoch, full)



def calculate_duration_from_to(fromm:float, to: float, full: bool=True) -> str:
    if fromm is None or to is None or not isinstance(fromm, (int, float)) or not isinstance(to, (int, float)) :
        return None

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



def format_binaries(number: int, precision: int=2) -> str:
    if number is None or not isinstance(number, int):
        return None

    is_negative = number < 0
    if is_negative:
        number = -number

    # 2**10 = 1024
    divider = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB', 5: 'PB', 6: 'EB', 7: 'ZB', 8: 'YB'}
    while number > divider:
        number /= divider
        n += 1

    return ("-" if is_negative else "") + str(round(number, precision)) + power_labels[n]



def format_decimals(number: int, precision: int=2) -> str:
    if number is None or not isinstance(number, int):
        return None
    
    is_negative = number < 0
    if is_negative:
        number = -number

    divider = 1000
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'B', 4: 'T', 5: 'Qa', 6: 'Qi', 7: 'Sx', 8: 'Sp', 9: 'Oc'}
    while number > divider:
        number /= divider
        n += 1

    return ("-" if is_negative else "") + str(round(number, precision)) + power_labels[n]
