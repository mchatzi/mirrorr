#!/usr/bin/env python3
import argparse
import logging
import re
import subprocess
import sys
import json
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
import requests
import yaml
import os

SUCCESS = "SUCCESS"
PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
NOOP = "NOOP"
ABORTED = "ABORTED"
FAILED = "FAILED"

JOB_LOG_ROTATION_LIMIT = 10
WEB_LOGS_URL = ""

MIRRORR_JOB = {}
MIRRORR_CONF = {}

logger = logging.getLogger(__package__)

# The report should always contain all possible attributes
DEFAULT_REPORT_LOG_PAYLOAD = {
    "name": "Not set",
    "source": "Not set",
    "dest": "Not set",
    "allowed_percentage": -1,
    "total_files": -1,
    "deleted": -1,
    "created": -1,
    "transferred": -1,
    "bytes_transferred": -1,
    "duration": -1,
    "human_readable_duration": "Not set",
    "human_readable_bytes_transferred": "Not set",
    "status": -1,
    "exit_code": -1,
    "message": "Not set",
    "logfile_url": "Not set"
}


def main():
    send_heartbeat()
    begin = time.time()

    violations = validate_paths()
    if violations:
        job_finished(FAILED, 1, stderr='\n'.join(violations), started_at=begin)

    stdout, exit_code, stderr = run_rsync(dry_run=True)
    if exit_code not in (0, 23, 24):
        job_finished(FAILED, exit_code=exit_code, stderr=stderr, stdout=stdout, started_at=begin)

    stats = parse_rsync_stats(stdout)

    total_files_before = stats['total_files'] + stats['deleted']
    if total_files_before != 0:
        percentage_of_deleted = stats['deleted'] * 100 // total_files_before
        if percentage_of_deleted >= MIRRORR_JOB['allowed_percentage']:
            message = f"Too many files would be deleted ({percentage_of_deleted}%). Max allowed is {MIRRORR_JOB['allowed_percentage']}%"
            job_finished(ABORTED, 1, stderr=message, stats=stats, started_at=begin)

    # Proceed with non dry rsync (and replace the stats)
    if not MIRRORR_JOB['dryruns']:
        stdout, exit_code, stderr = run_rsync(dry_run=False)
        stats = parse_rsync_stats(stdout)

    if exit_code == 0:
        if stats['transferred'] + stats['deleted'] == 0:
            job_finished(NOOP, 0, stats=stats, started_at=begin)
        job_finished(SUCCESS, 0, stdout=stdout, stats=stats, started_at=begin)
    elif exit_code in (23,24):
        job_finished(PARTIAL_SUCCESS, exit_code, stderr=stderr, stdout=stdout, stats=stats, started_at=begin)
    else:
        job_finished(FAILED, exit_code=exit_code, stderr=stderr, stdout=stdout, started_at=begin)



def validate_paths() -> list:
    violations = []
    path_inputs = [("Source", MIRRORR_JOB['source']), ("Destination", MIRRORR_JOB['dest'])]

    for label, value in path_inputs:
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

    return violations if violations else []



def run_rsync(dry_run: bool = True) -> (str, int, str):
    command = []

    if MIRRORR_JOB['rsync_nice']:
        command += ["nice", "-n", str(MIRRORR_JOB['rsync_nice'])]
    if MIRRORR_JOB['rsync_ionice']:
        command += ["ionice", str(MIRRORR_JOB['rsync_ionice'])]

    command += ["rsync", "--recursive", "--links", "--info=stats2"]

    command.append("--no-owner" if MIRRORR_JOB["rsync_no_owner"] else "--owner")
    command.append("--no-group" if MIRRORR_JOB["rsync_no_group"] else "--group")
    command.append("--no-perms" if MIRRORR_JOB["rsync_no_perms"] else "--perms")
    command.append("--no-times" if MIRRORR_JOB["rsync_no_times"] else "--times")

    if MIRRORR_JOB['rsync_acls']:
        command.append("--acls")
    if MIRRORR_JOB['rsync_delete']:
        command.append("--delete")
    if MIRRORR_JOB['rsync_in_place']:
        command.append("--inplace")
    if MIRRORR_JOB['rsync_whole_file']:
        command.append("--whole-file")
    if MIRRORR_JOB['rsync_fsync']:
        command.append("--fsync")
    if MIRRORR_JOB['rsync_bwlimit']:
        command.append(f"--bwlimit={str(MIRRORR_JOB['rsync_bwlimit'])}")
    if dry_run:
        command.append("--dry-run")

    command += [MIRRORR_JOB['source'], MIRRORR_JOB['dest']]
    logger.debug(' '.join(command))

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"EXITCODE ----------->{result.returncode}<----------")
            logger.debug(f"STDOUT ----------->\n{result.stdout}<----------/////STDOUT")
            logger.debug(f"STDERR ----------->\n{result.stderr}<----------/////STDERR")

        return result.stdout, result.returncode, result.stderr
    except Exception as e:
        exc_msg = f"{e}"
        logger.error(f"Error! {exc_msg}")
        return "", 1, exc_msg



def parse_rsync_stats(rsync_output: str) -> dict:
    def extract(pattern):
        match = re.search(pattern, rsync_output)
        return match.group(1) if match else ""

    return {
        "total_files": int(extract(r'Number of files: ([\d,]+)').replace(",", "")),
        "deleted": int(extract(r'Number of deleted files: ([\d,]+)').replace(",", "")),
        "created": int(extract(r'Number of created files: ([\d,]+)').replace(",", "")),
        "transferred": int(extract(r'Number of regular files transferred: ([\d,]+)').replace(",", "")),
        "bytes_transferred": int(extract(r'Total transferred file size: (\S+) bytes')
                                 .replace(",", ""))
    }


def job_finished(status:str, exit_code:int, started_at:int, stderr:str = "", stdout:str = "", stats: dict = {}):
    stats |= {'logfile_url': WEB_LOGS_URL + urllib.parse.quote(MIRRORR_JOB['name'])}

    duration = int(time.time() - started_at)
    stats |= {'duration': duration}
    stats |= {'human_readable_duration': format_duration(duration)}
    stats |= {'human_readable_bytes_transferred': format_bytes(stats.get('bytes_transferred', 0))}

    status_label = f'{status}{" -- DRY RUN" if MIRRORR_JOB["dryruns"] else ""}'

    if status in [FAILED, ABORTED]:
        keep_a_log(f"{status_label}\n\nTook:{stats['human_readable_duration']}\nTransfered:{stats['human_readable_bytes_transferred']}\n\n{stderr}")
        report(status_label, exit_code, message=stderr, stats=stats)
        sys.exit(1)
    elif status == NOOP:
        if MIRRORR_JOB['log_noop']:
            keep_a_log(f"{status_label}\n\nNothing was transferred or deleted\n\nTook:{stats['human_readable_duration']}\nTransfered:{stats['human_readable_bytes_transferred']}")
        if MIRRORR_JOB['report_noop']:
            report(status_label, exit_code, message="Nothing was transferred or deleted", stats=stats)
        sys.exit(0)
    elif status == SUCCESS:
        if MIRRORR_JOB['log_success']:
            keep_a_log(f"{status_label}\n\nTook:{stats['human_readable_duration']}\nTransfered:{stats['human_readable_bytes_transferred']}\n\n{stdout}")
        if MIRRORR_JOB['report_success']:
            report(status_label, exit_code, message="All went well", stats=stats)
        sys.exit(0)
    elif status == PARTIAL_SUCCESS:
        keep_a_log(f"{status_label}\n\nTook:{stats['human_readable_duration']}\nTransfered:{stats['human_readable_bytes_transferred']}\n\n{stderr}\n\n{stdout}")
        # Don't send whole stderr, the last line contains what happened
        summary = (lambda lines: lines[-1] if lines else "")(str(stderr).splitlines())
        report(status_label, exit_code, stats=stats, message=summary)
        sys.exit(0)

    sys.exit(1)
    


def report(status: str, exit_code: int, message: str = "", stats: dict = None):
    report_payload = DEFAULT_REPORT_LOG_PAYLOAD | {
        "status": status,
        "exit_code": exit_code,
        "message": message
    }

    # Copy only keys we want
    report_payload |= {k:v for k,v in MIRRORR_JOB.items() if k in DEFAULT_REPORT_LOG_PAYLOAD}

    if stats:
        report_payload |= stats

    if MIRRORR_JOB["reporter_o2"]:
        try:
            notify_o2(report_payload)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send log to o2: {e}")

    if MIRRORR_JOB['reporter_discord']:
        try:
            notify_discord(report_payload)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to notify discord: {e}")


def notify_o2(report_payload: dict):
    if 'o2_reporter' not in MIRRORR_CONF:
        logger.error("OpenObserve reporter is not configured correctly")
    else:
        o2_url = MIRRORR_CONF["o2_reporter"].get("o2_server_url")
        o2_basic_auth = MIRRORR_CONF["o2_reporter"].get("o2_server_auth")

        if not o2_url or not o2_basic_auth:
            logger.error("OpenObserve reporter is not configured correctly")
        else:
            response = requests.post(o2_url, json=report_payload,
                                headers={"Content-Type": "application/x-www-form-urlencoded","Authorization": f"Basic {o2_basic_auth}"})
            response.raise_for_status()


def notify_discord(report_payload: dict):
    if 'discord_reporter' not in MIRRORR_CONF:
        logger.error("Discord reporter is not configured correctly")
    else:
        webhook_url = MIRRORR_CONF["discord_reporter"].get("webhook_url")
        template = MIRRORR_CONF["discord_reporter"].get("template")

        if not webhook_url or not template:
            logger.error("Discord reporter is not configured correctly")
        else:
            # TODO Document these extra attributes for the alert!
            now = datetime.now()
            report_payload |= {"timestamp": now.timestamp(), "timestamp_human_friendly": format_date(now)}

            #Interpolate
            [template := template.replace(
                "{" + placeholder + "}", json.dumps(str(value))[1:-1]) 
                for placeholder, value in report_payload.items()]

            response = requests.post(webhook_url, json=json.loads(template), headers={"Content-Type": "application/json"})
            response.raise_for_status()


def send_heartbeat():
    health_heartbeat_url = MIRRORR_CONF.get('health_heartbeat_url')

    if health_heartbeat_url:
        try:
            response = requests.get(health_heartbeat_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send heartbeat to url '{health_heartbeat_url}', error: {e}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
    else:
        logger.info("Health heartbeat is not configured")


def keep_a_log(stderr):
    # TODO Pass as parameter
    log_path = Path(f"{MIRRORR_CONF['job_logs_dir']}/{MIRRORR_JOB['name']}.log")

    if log_path.exists():
        rotate_job_logs(MIRRORR_JOB['name'])

    with open(log_path, "w") as log_file:
        print(f"Report created on {format_date(datetime.now())}\n", file=log_file)
        # TODO Also inform whether UptimeKuma got notified (check and record its return status code)
        print(f"{stderr}", file=log_file)


def rotate_job_logs(job_name, index: int = 0):
    log_path = get_log_path(job_name, index)

    if Path(log_path).exists():
        if index == JOB_LOG_ROTATION_LIMIT - 1:
            Path(log_path).unlink()
        else:
            rotate_job_logs(job_name, index + 1)

    if not Path(log_path).exists() and index > 0:
        Path(get_log_path(job_name, index - 1)).rename(log_path)


def get_log_path(job_name, index) -> str:
    postfix = '' if index == 0 else f".{index}"
    return f"{MIRRORR_CONF['job_logs_dir']}/{job_name}{postfix}.log"


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


def format_date(date) -> str:
    return date.strftime('%Y-%m-%d %H:%M:%S')


def create_mirrorr_conf(args):
    global MIRRORR_CONF
    global WEB_LOGS_URL

    mirrorr_conf = Path(args.conf)
    if not mirrorr_conf.exists():
        logger.error(f"File {mirrorr_conf.name} not found")
        sys.exit(1)

    with open(mirrorr_conf, 'r') as f:
        MIRRORR_CONF = yaml.safe_load(f)

    if not MIRRORR_CONF.get('server_address'):
        logger.info(f"Server address is not configured, auto-detected: {args.fqdn_or_ip}")
        WEB_LOGS_URL = f"http://{args.fqdn_or_ip}:5000/joblog.html?name="  
    else:
        WEB_LOGS_URL = f"{MIRRORR_CONF['server_address']}/joblog.html?name="

    MIRRORR_CONF['job_logs_dir'] = args.logsdir


def create_mirrorr_job(args):
    global MIRRORR_JOB

    job_conf = Path(args.job)
    if not job_conf.exists():
        logger.error(f"File {job_conf.name} not found")
        sys.exit(1)

    with open(job_conf, 'r') as f:
        MIRRORR_JOB = yaml.safe_load(f)


def setup_logging(args):
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d, %H:%M:%S')

    logger.setLevel(args.loglevel.upper())  # Set the logging level


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the logging level")
    parser.add_argument('-conf', help='Absolute path to mirrorr conf file', required=True)
    parser.add_argument('-job', help='Absolute path to job conf file', required=True)
    parser.add_argument('-loglevel', default='WARNING', help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',required=True)
    parser.add_argument('-fqdn_or_ip', help='Fully qualified domain name or IP of the mirrorr web server', required=True)
    parser.add_argument('-logsdir', help='Dir where the job logs should go', required=True)

    args = parser.parse_args()

    setup_logging(args)
    create_mirrorr_conf(args)
    create_mirrorr_job(args)

    main()
