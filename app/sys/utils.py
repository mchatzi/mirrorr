#!/usr/bin/env python3
import logging
from pathlib import Path
import logging
import re
from pathlib import Path
import os
import subprocess

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
    violations = []
    path_inputs = [("source", "Source", MIRRORR_JOB['source']), ("dest", "Destination", MIRRORR_JOB['dest'])]

    for name, label, value in path_inputs:
        if not MIRRORR_JOB.get(f"remote_{name}"):
            
            if MIRRORR_JOB.get("run_rsync_as_root", False):
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

    command.append("--no-owner" if MIRRORR_JOB.get("rsync_no_owner", False) else "--owner")
    command.append("--no-group" if MIRRORR_JOB.get("rsync_no_group", False) else "--group")
    command.append("--no-perms" if MIRRORR_JOB.get("rsync_no_perms", False) else "--perms")
    command.append("--no-times" if MIRRORR_JOB.get("rsync_no_times", False) else "--times")

    if MIRRORR_JOB.get('rsync_acls', False):
        command.append("--acls")
    if MIRRORR_JOB.get('rsync_delete', False):
        command.append("--delete")
    if MIRRORR_JOB.get('rsync_in_place', False):
        command.append("--inplace")
    if MIRRORR_JOB.get('rsync_whole_file', False):
        command.append("--whole-file")
    if MIRRORR_JOB.get('rsync_fsync', False):
        command.append("--fsync")
    if MIRRORR_JOB.get('rsync_verbose', False):
        command.append("--verbose")
    if MIRRORR_JOB.get('rsync_cvs_exclude', False):
        command.append("--cvs-exclude")
    if MIRRORR_JOB.get('rsync_compress', False):
        command.append("--compress")
    if MIRRORR_JOB.get('rsync_update', False):
        command.append("--update")
    if MIRRORR_JOB.get('rsync_prune_empty_dirs', False):
        command.append("--prune-empty-dirs")
    if MIRRORR_JOB.get('rsync_bwlimit'):
        command.append(f"--bwlimit={str(MIRRORR_JOB['rsync_bwlimit'])}")
    if dry_run:
        command.append("--dry-run")
    if MIRRORR_JOB.get('rsync_exclude'):
        for exclusion in MIRRORR_JOB['rsync_exclude'].split(','):
            command += ["--exclude", exclusion.strip()]
    if MIRRORR_JOB.get('remote_source') == True or MIRRORR_JOB.get('remote_dest') == True:
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
        return {
            "total_files": int(extract(r'Number of files: ([\d,]+)').replace(",", "")),
            "deleted": int(extract(r'Number of deleted files: ([\d,]+)').replace(",", "")),
            "created": int(extract(r'Number of created files: ([\d,]+)').replace(",", "")),
            "transferred": int(extract(r'Number of regular files transferred: ([\d,]+)').replace(",", "")),
            "bytes_transferred": int(extract(r'Total transferred file size: (\S+) bytes').replace(",", ""))
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
