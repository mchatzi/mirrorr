#!/usr/bin/env python3
import logging
from pathlib import Path
import logging
import re
from pathlib import Path
import os

MIRRORR_JOB = {}
logger = logging.getLogger("mirrorr")


def validate_paths() -> list:
    violations = []
    path_inputs = [("source", "Source", MIRRORR_JOB['source']), ("dest", "Destination", MIRRORR_JOB['dest'])]

    for name, label, value in path_inputs:
        if not MIRRORR_JOB.get(f"remote_{name}"):
            try:
                path = Path(value)
                if not path.exists():
                    violations.append(f"{label} path ({value}) is not resolvable" )
                if not os.access(path, os.X_OK):
                    violations.append(f"{label} path ({value}) is not traversable")
                if label == "Source" and not os.access(path, os.R_OK):
                    violations.append(f"{label} path ({value}) is not readable")
                if label == "Destination" and not os.access(path, os.W_OK):
                    violations.append(f"{label} path ({value}) is not writable")
            except PermissionError:
                violations.append(f"Permission denied for {label} path ({value})")
        else:
            if not re.search(r"^[^:@\s]+@[^:/\s]+:/\S+$", value):
                violations.append(f"{label} ({value}): not a valid scp address. Use this format: user@server:/folder/")

    return violations if violations else []


def parse_rsync_stats(rsync_output: str) -> dict:
    def extract(pattern):
        match = re.search(pattern, rsync_output)
        return match.group(1) if match else ""

    try:
        return {
            "total_files": int(extract(r'Number of files: ([\d,]+)').replace(",", "")),
            "deleted": int(extract(r'Number of deleted files: ([\d,]+)').replace(",", "")),
            "created": int(extract(r'Number of created files: ([\d,]+)').replace(",", "")),
            "transferred": int(extract(r'Number of regular files transferred: ([\d,]+)').replace(",", "")),
            "bytes_transferred": int(extract(r'Total transferred file size: (\S+) bytes')
                                    .replace(",", ""))
        }
    except Exception as e:
        exc_msg = f"{e}"
        logger.warning(f"Error parsing rsync logs! {exc_msg}")
        logger.warning("Rsync logs:")
        logger.warning(rsync_output)
        return None



def format_duration(duration_in_seconds: int):
    hours, remainder = divmod(duration_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return ''.join(f"{value}{label}" for value, label in
                   ((hours, "h"), (minutes, "m"), (seconds, "s")) if value or (label == "s"))


def format_bytes(bytes_transferred: int) -> str:
    if bytes_transferred == -1:
        return "Not set"

    # 2**10 = 1024
    power = 2 ** 10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while bytes_transferred > power:
        bytes_transferred /= power
        n += 1

    return str(round(bytes_transferred, 2)) + power_labels[n]
