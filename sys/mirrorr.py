#!/usr/bin/env python3
import argparse
import logging
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests
import yaml

SUCCESS = "SUCCESS"
PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
NOOP = "NOOP"
ABORTED = "ABORTED"
FAILED = "FAILED"

JOB_LOG_ROTATION_LIMIT = 10

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
    "reason": "Not set",
    "logfile_url": "Not set"
}


def main():
    dryrun_stdout, exit_code, stderr = run_rsync(dry_run=True)
    dryrun_stats = parse_rsync_stats(dryrun_stdout)

    if dryrun_stats['transferred'] + dryrun_stats['deleted'] == 0:
        # Nothing was transferred and nothing was deleted
        # TODO Do we really report this? We don't even keep a log...
        report(NOOP, 0, stats=dryrun_stats)
        sys.exit(0)

    total_files_before = dryrun_stats['total_files'] + dryrun_stats['deleted']
    percentage_of_deleted = dryrun_stats['deleted'] * 100 // total_files_before

    if percentage_of_deleted >= MIRRORR_JOB['allowed_percentage']:
        reason = f"Too many files would be deleted ({percentage_of_deleted}%). Max allowed is {MIRRORR_JOB['allowed_percentage']}%"
        keep_a_log("ABORTED\n\n" + reason)
        dryrun_stats['logfile_url'] = MIRRORR_CONF["mirrorr_web_url"] + urllib.parse.quote(MIRRORR_JOB['name'])
        report(ABORTED, 1, reason=reason, stats=dryrun_stats)
    else:
        begin = time.time()
        stdout, exit_code, stderr = run_rsync(dry_run=False)
        end = time.time()

        stats = parse_rsync_stats(stdout)

        duration = int(end - begin)
        stats['duration'] = duration
        stats['human_readable_duration'] = format_duration(duration)

        stats['human_readable_bytes_transferred'] = format_bytes(stats['bytes_transferred'])

        logger.debug("STDOUT=" + stdout + "////////////////////////////////STDOUT\n\n")
        logger.debug("STDERR=" + stderr + "////////////////////////////////STDERR\n\n")

        if exit_code == 0:
            keep_a_log("SUCCESS\n\n" + stdout)
            stats['logfile_url'] = MIRRORR_CONF["mirrorr_web_url"] + urllib.parse.quote(MIRRORR_JOB['name'])
            report(SUCCESS, exit_code, stats=stats)
        else:
            keep_a_log("PARTIAL SUCCESS\n\n" + stderr)
            stats['logfile_url'] = MIRRORR_CONF["mirrorr_web_url"] + urllib.parse.quote(MIRRORR_JOB['name'])

            # Don't send whole stderr, the last line contains what happened
            summary = (lambda lines: lines[-1] if lines else "")(str(stderr).splitlines())

            report(PARTIAL_SUCCESS, exit_code, stats=stats, reason=summary)


def parse_rsync_stats(rsync_output: str):
    def extract(pattern):
        match = re.search(pattern, rsync_output)
        return match.group(1) if match else ""

    return {
        "total_files": int(extract(r'Number of files: (\d+)')),
        "deleted": int(extract(r'Number of deleted files: (\d+)')),
        "created": int(extract(r'Number of created files: (\d+)')),
        "transferred": int(extract(r'Number of regular files transferred: (\d+)')),
        "bytes_transferred": int(extract(r'Total transferred file size: (\S+) bytes')
                                 .replace(",", ""))
    }


def report(status: str, exit_code: int, reason: str = "", stats: dict = None):
    report_payload = DEFAULT_REPORT_LOG_PAYLOAD | {
        "status": status,
        "exit_code": exit_code,
        "reason": reason
    }

    # Copy only keys we want
    report_payload |= {k:v for k,v in MIRRORR_JOB.items() if k in DEFAULT_REPORT_LOG_PAYLOAD}

    if stats:
        report_payload |= stats

    if MIRRORR_JOB["reporter_o2"]:
        o2_url = MIRRORR_CONF["o2_reporter"]["o2_server_url"]
        o2_basic_auth = MIRRORR_CONF["o2_reporter"]["o2_server_auth"]

        if not o2_url or not o2_basic_auth:
            logger.error("OpenObserve reporter is not configured correctly")
        else:
            try:
                notify_o2(o2_url, o2_basic_auth, report_payload)
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to send log to o2: {e}")

    #if MIRRORR_JOB['reporter_discord']:



def notify_o2(o2_url: str, o2_basic_auth: str, report_payload: dict):
    response = requests.post(o2_url, json=report_payload,
                             headers={"Content-Type": "application/x-www-form-urlencoded",
                                      "Authorization": f"Basic {o2_basic_auth}"})
    response.raise_for_status()



def run_rsync(dry_run: bool = True):
    try:
        # command = ["rsync", "--archive", "--info=stats2", "--delete", "--no-owner", "--no-perms", "--no-group", MIRRORR_JOB['source'], MIRRORR_JOB['dest']]
        command = ["rsync", "--archive", "--info=stats2", "--delete", "--no-owner", "--no-perms", MIRRORR_JOB['source'],
                   MIRRORR_JOB['dest']]
        # "--fsync",

        if dry_run:
            command.append("--dry-run")

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            return result.stdout, 0, result.stderr

        if result.returncode in (23, 24):
            return result.stdout, result.returncode, result.stderr

        keep_a_log("FAILED\n\n" + result.stderr)
        report(FAILED, reason=result.stderr, exit_code=result.returncode, stats={'logfile_url': MIRRORR_CONF["mirrorr_web_url"] + urllib.parse.quote(MIRRORR_JOB['name'])})
        sys.exit(1)
    except Exception as e:
        exc_msg = f"{e}"
        logger.error(exc_msg)
        keep_a_log("FAILED\n\n" + exc_msg)
        report(FAILED, 1, reason=exc_msg, stats={'logfile_url': MIRRORR_CONF["mirrorr_web_url"] + urllib.parse.quote(MIRRORR_JOB['name'])})
        sys.exit(1)


def keep_a_log(stderr):
    # TODO Pass as parameter
    log_path = Path(f"{MIRRORR_CONF['job_logs_dir']}/{MIRRORR_JOB['name']}.log")

    if log_path.exists():
        rotate_job_logs(MIRRORR_JOB['name'])

    with open(log_path, "w") as log_file:
        print(f"Report created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", file=log_file)
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


def get_log_path(job_name, index):
    postfix = '' if index == 0 else f".{index}"
    return f"{MIRRORR_CONF['job_logs_dir']}/{job_name}{postfix}.log"


def format_duration(duration_in_seconds: int):
    hours, remainder = divmod(duration_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return ''.join(f"{value}{label}" for value, label in
                   ((hours, "h"), (minutes, "m"), (seconds, "s")) if value or (label == "s"))


def format_bytes(bytes_transferred: int):
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


def create_mirrorr_conf(args):
    global MIRRORR_CONF

    mirrorr_conf = Path(args.conf)
    if not mirrorr_conf.exists():
        logger.error(f"File {mirrorr_conf.name} not found")
        sys.exit(1)

    with open(mirrorr_conf, 'r') as f:
        MIRRORR_CONF = yaml.safe_load(f)

    MIRRORR_CONF["mirrorr_web_url"] = f"http://{args.ip}:5000/joblog.html?name="
    MIRRORR_CONF["job_logs_dir"] = args.logsdir


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
    parser.add_argument('-ip', help='IP of the mirrorr web server', required=True)
    parser.add_argument('-logsdir', help='Dir where the job logs should go', required=True)

    args = parser.parse_args()

    setup_logging(args)
    create_mirrorr_conf(args)
    create_mirrorr_job(args)

    main()
