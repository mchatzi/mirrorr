#!/usr/bin/env python3
import logging
import json
from datetime import datetime
import requests
from pathlib import Path
import sys


MIRRORR_JOB = {}
MIRRORR_CONF = {}
logger = logging.getLogger("mirrorr")

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


def format_date(date) -> str:
    return date.strftime('%Y-%m-%d %H:%M:%S')


def write_job_log(log_message):
    log_path = Path(get_log_path(MIRRORR_JOB['name']))

    if log_path.exists():
        rotate_job_logs(MIRRORR_JOB['name'])

    with open(log_path, "w") as log_file:
        print(f"Report created on {format_date(datetime.now())}\n", file=log_file)
        # TODO Also inform whether UptimeKuma got notified (check and record its return status code)
        print(f"{log_message}", file=log_file)


def rotate_job_logs(job_name, index: int = 0):
    log_path = get_log_path(job_name, index)
    log_retention_count = int(MIRRORR_CONF['log_retention_count']) if 'log_retention_count' in MIRRORR_CONF else 10


    if Path(log_path).exists():
        if index == log_retention_count - 1:
            Path(log_path).unlink()
        else:
            rotate_job_logs(job_name, index + 1)

    if not Path(log_path).exists() and index > 0:
        Path(get_log_path(job_name, index - 1)).rename(log_path)


def get_log_path(job_name, index: int = 0) -> str:
    postfix = '' if index == 0 else f".{index}"
    return f"{MIRRORR_CONF['job_logs_dir']}/{job_name}{postfix}.log"


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
