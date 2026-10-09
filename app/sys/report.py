#!/usr/bin/env python3
import logging
import json
from datetime import datetime
import requests
from pathlib import Path
import sys


MIRRORR_JOB = {}
MIRRORR_CONF = {}
DATA_DIR = None
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
    "logfile_url": "Not set",
    "environment": "Not set"
}


def report(status: str, exit_code: int, message: str = "", stats: dict = None) -> int:
    report_payload = DEFAULT_REPORT_LOG_PAYLOAD | {
        "status": status,
        "exit_code": exit_code,
        "message": message
    }

    if MIRRORR_CONF.get('environment'):
        report_payload |= { "environment": MIRRORR_CONF.get('environment')}

    # Copy only keys we want
    report_payload |= {k:v for k,v in MIRRORR_JOB.items() if k in DEFAULT_REPORT_LOG_PAYLOAD}

    if stats:
        report_payload |= stats

    if MIRRORR_JOB["reporter_o2"]:
        try:
            notify_o2(report_payload)
        except Exception as e:
            logger.error(f"Failed to send log to o2: {e}")
            return 1

    if MIRRORR_JOB['reporter_discord']:
        try:
            notify_discord(report_payload)
        except Exception as e:
            logger.error(f"Failed to notify discord: {e}")
            return 1
    
    if MIRRORR_JOB['reporter_custom']:
        try:
            notify_custom_reporter(report_payload)
        except Exception as e:
            logger.error(f"Failed to notify custom reporter: {e}")
            return 1
    
    return 0


def notify_o2(report_payload: dict):
    if 'o2_reporter' not in MIRRORR_CONF:
        logger.error("OpenObserve reporter is not configured")
    else:
        o2_url = MIRRORR_CONF["o2_reporter"].get("o2_server_url")
        o2_basic_auth = MIRRORR_CONF["o2_reporter"].get("o2_server_auth")

        if not o2_url or not o2_basic_auth:
            logger.error("OpenObserve reporter is not configured correctly")
            return

        logger.debug("Reporting to OpenObserve. Payload:")
        logger.debug(repr(report_payload))

        response = requests.post(o2_url, json=report_payload, headers={
                            "Content-Type": "application/json", 
                            "Authorization": f"Basic {o2_basic_auth}", 
                            "User-Agent": "Mirrorr via python-requests"})
        response.raise_for_status()


def notify_discord(report_payload: dict):
    if 'discord_reporter' not in MIRRORR_CONF:
        logger.error("Discord reporter is not configured")
    else:
        webhook_url = MIRRORR_CONF["discord_reporter"].get("webhook_url")
        template_str = MIRRORR_CONF["discord_reporter"].get("template")

        if not webhook_url or not template_str:
            logger.error("Discord reporter is not configured correctly")
            return

        now = datetime.now()
        report_payload |= {"timestamp": now.timestamp(), "timestamp_human_friendly": format_date(now)}

        if isinstance(MIRRORR_CONF["discord_reporter"].get("truncate_after", None), int):
            limit = MIRRORR_CONF["discord_reporter"].get("truncate_after") - 3
            for key, value in report_payload.items():
                report_payload[key] = value[:limit] + "..." if isinstance(value, str) and len(value) > 197 else value      

        if MIRRORR_CONF["discord_reporter"].get("auto_json", True):
            for key, value in report_payload.items():
                report_payload[key] = json.dumps(value)[1:-1] if isinstance(value, str) else value;

        from jinja2 import Environment, StrictUndefined
        rendered = Environment(undefined=StrictUndefined) \
            .from_string(template_str) \
            .render(report_payload)

        logger.debug("Reporting to Discord. Payload:\n" + rendered)
        response = requests.post(webhook_url, json=json.loads(rendered), headers={
            "Content-Type": "application/json", 
            "User-Agent": "Mirrorr via python-requests"})
        response.raise_for_status()


def notify_custom_reporter(report_payload: dict):
    if 'custom_reporter' not in MIRRORR_CONF:
        logger.error("Custom reporter is not configured")
    else:
        custom_reporter_server_url = MIRRORR_CONF["custom_reporter"].get("server_url")
        method = MIRRORR_CONF["custom_reporter"].get("method")

        if not custom_reporter_server_url or not method:
            logger.error("Custom reporter is not configured correctly")
            return

        json_param = MIRRORR_CONF["custom_reporter"].get("json_param")
        headers = MIRRORR_CONF["custom_reporter"].get("headers")
        headers_dict = {"User-Agent": "Mirrorr via python-requests"}

        if headers:
            headers_dict |= dict(                
                item.strip().split(": ", 1)                
                for item in headers.split(", "))

        logger.debug("Reporting to Custom reporter. Payload:")
        logger.debug(repr(report_payload))

        if method == "GET":
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(custom_reporter_server_url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            params[json_param or 'json'] = json.dumps(report_payload)
            custom_reporter_server_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
            logger.debug(repr(custom_reporter_server_url))
            response = requests.get(custom_reporter_server_url, headers=headers_dict)
        elif method == "POST":
            if json_param:
                headers_dict |= {"Content-Type": "application/x-www-form-urlencoded"}
                data = {json_param: json.dumps(report_payload)}
                response = requests.post(custom_reporter_server_url, data=data, headers=headers_dict)
            else:
                headers_dict |= {"Content-Type": "application/json"}
                response = requests.post(custom_reporter_server_url, json=report_payload, headers=headers_dict)

        response.raise_for_status()


def format_date(date) -> str:
    return date.strftime('%Y-%m-%d %H:%M:%S')


def write_job_log(log_message):
    log_path = Path(get_log_path(MIRRORR_JOB['name']))

    if log_path.exists():
        rotate_job_logs(MIRRORR_JOB['name'])

    with open(log_path, "w") as log_file:
        print(f"Report for {MIRRORR_JOB['name']}", file=log_file)
        print(f"{format_date(datetime.now())}" + \
            (f", {MIRRORR_CONF.get('environment')}" if MIRRORR_CONF.get('environment', None) else ''), file=log_file)

        # TODO Also inform whether UptimeKuma got notified (check and record its return status code)
        print(f"\n{log_message}", file=log_file)


def rotate_job_logs(job_name, index: int = 0):
    log_path = get_log_path(job_name, index)
    log_retention_count = int(MIRRORR_JOB['log_retention_count']) if 'log_retention_count' in MIRRORR_JOB else 10


    if Path(log_path).exists():
        if index == log_retention_count - 1:
            Path(log_path).unlink()
        else:
            rotate_job_logs(job_name, index + 1)

    if not Path(log_path).exists() and index > 0:
        Path(get_log_path(job_name, index - 1)).rename(log_path)


def get_log_path(job_name, index: int = 0) -> str:
    postfix = '' if index == 0 else f".{index}"
    return f"{DATA_DIR}/logs/{job_name}{postfix}.log"


def get_temp_job_out_log_path() -> str:
    return f"{DATA_DIR}/.runtime/{MIRRORR_JOB['name']}_out.log"


def get_temp_job_err_log_path() -> str:
        return f"{DATA_DIR}/.runtime/{MIRRORR_JOB['name']}_err.log"


#TODO This wont scale 
def fully_load_log(path) -> str:
    log = Path(path)

    if log.exists():
        with open(log, "r") as log:
            return log.read()
    else:
        logger.error(f"FILE {path} NOT FOUND")
        return f"FILE {path} NOT FOUND"


def send_heartbeat(status:str, exit_code:int, reporters_exit_code:int, duration: int):
    heartbeat_conf = MIRRORR_CONF.get('heartbeat', {})
    health_heartbeat_url = heartbeat_conf.get("health_heartbeat_url", "")
    send_job_status = heartbeat_conf.get("send_job_status", False)
    send_reporters_status = heartbeat_conf.get('send_reporters_status', False)

    if health_heartbeat_url:
        if send_job_status or send_reporters_status:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(health_heartbeat_url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            params["status"] = ["up"]
            params["msg"] = [f"{MIRRORR_JOB.get('name')} completed with status {status}"] if send_job_status else "OK"
            params["ping"] = [ str(duration)]

            if send_job_status and exit_code not in (0, 20, 23, 24):
                params["status"] = ["down"]
            elif send_reporters_status and reporters_exit_code != 0:
                params["status"] = ["down"]
                params["msg"] = [f"A reporter has failed to run with exit code {reporters_exit_code}. The job {MIRRORR_JOB.get('name')} completed with status {status}"]

            health_heartbeat_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))

        try:
            response = requests.get(health_heartbeat_url)
            response.raise_for_status()
        except Exception as e:
            error_msg = f"Failed to send heartbeat to url '{health_heartbeat_url}', error: {e}"
            logger.error(error_msg)
    else:
        logger.info("Health heartbeat is not configured")
