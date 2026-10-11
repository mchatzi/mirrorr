#!/usr/bin/env python3
import logging
from pathlib import Path
import logging
import re
from pathlib import Path
import os
import subprocess
import time

MIRRORR_JOB = {}
MIRRORR_CONF = {}
logger = logging.getLogger("mirrorr")


def root_test(path, flag):
    command = ["sudo", "-S"]
    if "usergroups" in MIRRORR_CONF:
        command += ["setpriv", "--reuid=root", "--regid=root", f"--groups={MIRRORR_CONF['usergroups']}"]
    command += ["test", flag, path]

    return subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def validate_paths() -> list:
    logger.debug(f"Validating paths for {MIRRORR_JOB['name']}")

    violations = []
    path_inputs = [("source", "Source", MIRRORR_JOB['source']), ("dest", "Destination", MIRRORR_JOB['dest'])]

    for name, label, value in path_inputs:
        if not MIRRORR_JOB.get(f"remote_{name}"):
            
            if MIRRORR_JOB.get("run_rsync_as_root"):
                try:
                    if not root_test(value, "-e"):
                        violations.append(f"{label} path ({value}) is not resolvable" )
                    if root_test(value, "-d") and not root_test(value, "-x"):
                        violations.append(f"{label} path ({value}) is not traversable")
                    if name == "source" and not root_test(value, "-r"):
                        violations.append(f"{label} path ({value}) is not readable")
                    if name == "dest" and not root_test(value, "-w"):
                        violations.append(f"{label} path ({value}) is not writable")

                except PermissionError:
                    violations.append(f"Permission denied for {label} path ({value})")
            else:
                try:
                    path = Path(value)
                    if not path.exists():
                        violations.append(f"{label} path ({value}) is not resolvable" )
                    if path.is_dir() and not os.access(path, os.X_OK):
                        violations.append(f"{label} path ({value}) is not traversable")
                    if name == "source" and not os.access(path, os.R_OK):
                        violations.append(f"{label} path ({value}) is not readable")
                    if name == "dest" and not os.access(path, os.W_OK):
                        violations.append(f"{label} path ({value}) is not writable")
                except PermissionError:
                    violations.append(f"Permission denied for {label} path ({value})")
        else:
            if not re.search(r"^[^:@\s]+@[^:/\s]+:/\S+$", value):
                violations.append(f"{label} ({value}): not a valid scp address. Use this format: user@server:/folder/")

    return violations if violations else []


def create_rsync_command(dry_run: bool = True) -> list:
    #from mirrorr import MIRRORR_USER_GROUPS
    command = []

    if MIRRORR_JOB.get('run_rsync_as_root'):
        command += ["sudo", "-S"]
        if "usergroups" in MIRRORR_CONF:
            groups = ','.join(groupname.strip() for groupname in MIRRORR_CONF['usergroups'].split(","))
            command += ["setpriv", "--reuid=root", "--regid=root", f"--groups={groups}"]

    if MIRRORR_JOB.get('wrap_with_nice'):
        command += ["nice", "-n", str(MIRRORR_JOB['wrap_with_nice'])]
    if MIRRORR_JOB.get('wrap_with_ionice'):
        command += ["ionice", str(MIRRORR_JOB['wrap_with_ionice'])]

    command += ["rsync", "--recursive", "--links", "--info=stats2"]

    command.append("--no-owner" if MIRRORR_JOB.get("rsync_no_owner") else "--owner")
    command.append("--no-group" if MIRRORR_JOB.get("rsync_no_group") else "--group")
    command.append("--no-perms" if MIRRORR_JOB.get("rsync_no_perms") else "--perms")
    command.append("--no-times" if MIRRORR_JOB.get("rsync_no_times") else "--times")

    if MIRRORR_JOB.get('rsync_acls'):
        command.append("--acls")
    if MIRRORR_JOB.get('rsync_delete'):
        command.append("--delete")
    if MIRRORR_JOB.get('rsync_in_place'):
        command.append("--inplace")
    if MIRRORR_JOB.get('rsync_whole_file'):
        command.append("--whole-file")
    if MIRRORR_JOB.get('rsync_fsync'):
        command.append("--fsync")
    if MIRRORR_JOB.get('rsync_verbose'):
        command.append("--verbose")
    if MIRRORR_JOB.get('rsync_cvs_exclude'):
        command.append("--cvs-exclude")
    if MIRRORR_JOB.get('rsync_compress'):
        command.append("--compress")
    if MIRRORR_JOB.get('rsync_update'):
        command.append("--update")
    if MIRRORR_JOB.get('rsync_prune_empty_dirs'):
        command.append("--prune-empty-dirs")
    if MIRRORR_JOB.get('rsync_bwlimit'):
        command.append(f"--bwlimit={str(MIRRORR_JOB['rsync_bwlimit'])}")
    if dry_run:
        command.append("--dry-run")
    if MIRRORR_JOB.get('rsync_exclude'):
        for exclusion in MIRRORR_JOB['rsync_exclude'].split(','):
            command += ["--exclude", exclusion.strip()]
    if MIRRORR_JOB.get('remote_source') or MIRRORR_JOB.get('remote_dest'):
        remote_ssh_port = 22;
        if not MIRRORR_CONF.get('remote_ssh_port'):
            logger.warning(f"Remote ssh port not configured, using default ({remote_ssh_port})")
        else:
            remote_ssh_port = str(MIRRORR_CONF['remote_ssh_port'])
        command += ["-e", f"ssh -i /opt/mirrorr/data/ssh/id_ed25519 -p {remote_ssh_port} -o UserKnownHostsFile=/opt/mirrorr/data/ssh/known_hosts"]

    command.append(MIRRORR_JOB['source'])
    command.append(MIRRORR_JOB['dest'])

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Created rsync command for {MIRRORR_JOB['name']}:")
        logger.debug(repr(command))

    return command


def parse_rsync_stats(rsync_output: str) -> dict:
    def extract(pattern):
        match = re.search(pattern, rsync_output)
        return match.group(1) if match else ""

    try:
        total_files = int(extract(r'Number of files: ([\d,]+)').replace(",", ""))
        if total_files < 0:
            total_files = 0

        deleted = int(extract(r'Number of deleted files: ([\d,]+)').replace(",", ""))
        if deleted < 0:
            deleted = 0

        created = int(extract(r'Number of created files: ([\d,]+)').replace(",", ""))
        if created < 0:
            created = 0

        transferred = int(extract(r'Number of regular files transferred: ([\d,]+)').replace(",", ""))
        if transferred < 0:
            transferred = 0

        bytes_transferred = int(extract(r'Total transferred file size: (\S+) bytes').replace(",", ""))
        if bytes_transferred < 0:
            bytes_transferred = 0

        return {
            "total_files": total_files,
            "deleted": deleted,
            "created": created,
            "transferred": transferred,
            "bytes_transferred": bytes_transferred
        }
    except Exception as e:
        exc_msg = f"{e}"
        logger.warning(f"Error parsing rsync logs! {exc_msg}")
        logger.warning("Rsync logs:")
        logger.warning(rsync_output)
        return None



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



    return str(round(bytes_transferred, 2)) + power_labels[n]
