#!/usr/bin/env python3
from copy import deepcopy
import logging
import json
from datetime import datetime
import requests
from pathlib import Path
import yaml


MIRRORR_JOB = {}
MIRRORR_CONF = {}
DATA_DIR = None
logger = logging.getLogger("mirrorr")

# The report should always contain all possible attributes
DEFAULT_REPORT_LOG_PAYLOAD = {
    "name": "Not set",
    "source": "Not set",
    "dest": "Not set",
    "allowed_percentage": None,
    "total_files": 0,
    "deleted": 0,
    "created": 0,
    "transferred": 0,
    "bytes_transferred": 0,
    "bytes_transferred_human_readable": "0",
    "duration": 0,
    "duration_human_readable": "0",
    "status": "Not set",
    "exit_code": None,
    "message": "Not set",
    "logfile_url": "Not set",
    "environment": "Not set",
    "report_timestamp": None,
    "report_timestamp_human_readable": "Not set"
}


DEFAULT_EMPTY_STATISTICS = {
    "total_executions": 0,
    "total_executions_human_readable": "0",
    "total_executions_duration": 0,
    "total_executions_duration_human_readable": "0",            
    "total_bytes_transferred": 0,
    "total_bytes_transferred_human_readable": "0",
    "total_noops": 0,
    "total_successes": 0,
    "total_fails": 0,
    "total_reporters_fails": 0,
    "last_job_name": None,
    "last_job_exit_code": None,
    "last_reporters_exit_code": None,
    "last_updated_at": None,
    "last_updated_at_human_readable": None       
}
}


def report(status: str, exit_code: int, message: str = "", stats: dict = None) -> int:
    from utils import format_date

    if not MIRRORR_CONF.get('reporters'):
        logger.debug("No reporters configured")
        return 0

    if not MIRRORR_JOB.get('enabled_reporters'):
        return 0

    report_payload = DEFAULT_REPORT_LOG_PAYLOAD | {
        "status": status,
        "exit_code": exit_code,
        "message": message
    }

    if MIRRORR_CONF.get('environment'):
        report_payload |= { "environment": MIRRORR_CONF.get('environment')}

    # Copy only keys we want
    report_payload |= {k:v for k,v in MIRRORR_JOB.items() if k in DEFAULT_REPORT_LOG_PAYLOAD}

    now = datetime.now()
    report_payload |= {"report_timestamp": now.timestamp(), "report_timestamp_human_readable": format_date(now)}

    if stats:
        report_payload |= stats

    all_reporters_exit_code = 0
    enabled_reporters = [value.strip() for value in MIRRORR_JOB.get('enabled_reporters', '').split(',') if value.strip()]
    for endpoint in MIRRORR_CONF.get('reporters'):    
        try:
            if endpoint["name"] in enabled_reporters:
                notify_endpoint(endpoint, report_payload)
        except Exception as e:
            logger.error(f"Failed to notify reporter {endpoint.get('name') or 'No name'}: {e}")
            all_reporters_exit_code = 1

    return all_reporters_exit_code


def notify_endpoint(reporter, report_payload: dict):
    name = reporter.get("name") or "No name"
    endpoint_url = reporter.get("endpoint")
    method = reporter.get("method")

    if not endpoint_url or not method:
        logger.error(f"Reporter {name} is not configured correctly")
        return

    parameter_name = reporter.get("parameter_name")
    headers_dict = build_headers(reporter.get("headers")) 

    rendered_report_str = render_report(reporter.get("template"), report_payload) \
        if reporter.get("template") else json.dumps(report_payload)
    
    logger.debug(f"Reporting to {name}. Payload:")

    if method == "GET":
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(endpoint_url)
        params = parse_qs(parsed.query, keep_blank_values=True)

        if parameter_name or not reporter.get("template"):
            params[parameter_name or 'report'] = rendered_report_str
            endpoint_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
        else:
            endpoint_url = urlunparse(parsed._replace(query='', fragment=''))
            endpoint_url += "?" + rendered_report_str
        
        logger.debug(repr(headers_dict))
        logger.debug(endpoint_url)
        response = requests.get(endpoint_url, headers=headers_dict)
    elif method == "POST":
        if parameter_name:
            headers_dict |= {"Content-Type": "application/x-www-form-urlencoded"}
            logger.debug(repr(headers_dict))
            data = {parameter_name: rendered_report_str}
            logger.debug(repr(data))
            response = requests.post(endpoint_url, data=data, headers=headers_dict)
        else:
            headers_dict |= {"Content-Type": "application/json"}
            logger.debug(repr(headers_dict))
            if not reporter.get("template"):
                logger.debug(repr(report_payload))
                response = requests.post(endpoint_url, json=report_payload, headers=headers_dict)
            else:
                logger.debug(rendered_report_str)
                response = requests.post(endpoint_url, json=json.loads(rendered_report_str), headers=headers_dict)

    response.raise_for_status()


def build_headers(header_str) -> dict:
    headers_dict = {"User-Agent": "Mirrorr via python-requests"}
    if header_str:
        headers_dict |= dict(                
            item.strip().split(": ", 1)                
            for item in header_str.split(", "))
    return headers_dict


def render_report(template: str, report_payload) -> str:
    from jinja2 import Environment, StrictUndefined
    return Environment(undefined=StrictUndefined) \
        .from_string(template) \
        .render(report_payload)



def write_job_log(log_message):
    from utils import format_date

    log_path = Path(get_log_path(MIRRORR_JOB['name']))
    if log_path.exists():
        rotate_job_logs(MIRRORR_JOB['name'])

    with open(log_path, "w") as log_file:
        print(f"Report for {MIRRORR_JOB['name']}", file=log_file)
        print(f"{format_date(datetime.now())}" + \
            (f", {MIRRORR_CONF.get('environment')}" if MIRRORR_CONF.get('environment') else ''), file=log_file)

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
    heartbeat_conf = MIRRORR_CONF.get('heartbeat') or {}
    health_heartbeat_url = heartbeat_conf.get("health_heartbeat_url") or ""
    send_job_status = heartbeat_conf.get("send_job_status") or False
    send_reporters_status = heartbeat_conf.get('send_reporters_status') or False

    if health_heartbeat_url:
        if send_job_status or send_reporters_status:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(health_heartbeat_url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            params["ping"] = [ str(duration)]

            msg = ""
            if send_job_status and exit_code not in (0, 20, 23, 24) or \
                send_reporters_status and reporters_exit_code != 0:
                params["status"] = ["down"]
                msg = "NOT OK"
            else:
                 params["status"] = ["up"]
                 msg = "OK"

            if send_job_status:
                msg += f". {MIRRORR_JOB.get('name')} completed with status {status}"
            if send_reporters_status:
                msg += f". Reporters for {MIRRORR_JOB.get('name')} completed, exit code: {reporters_exit_code}"

            params["msg"] = [msg]

            health_heartbeat_url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))

        try:
            response = requests.get(health_heartbeat_url)
            response.raise_for_status()
        except Exception as e:
            error_msg = f"Failed to send heartbeat to url '{health_heartbeat_url}', error: {e}"
            logger.error(error_msg)
    else:
        logger.info("Health heartbeat is not configured")



def update_statistics(exit_code: int, status: str, duration: int, bytes_transferred: int, reporters_exit_code: int):
    from utils import format_binaries, format_duration, format_date, format_decimals

    mirrorr_stats = deepcopy(DEFAULT_EMPTY_STATISTICS)

    mirrorr_stats_file = Path(MIRRORR_CONF['stats_path']);
    if mirrorr_stats_file.exists():
        with open(mirrorr_stats_file, 'r') as f:
            mirrorr_stats = yaml.safe_load(f) or {}

    mirrorr_stats["total_executions"] = mirrorr_stats["total_executions"] + 1 if "total_executions" in mirrorr_stats else 1
    mirrorr_stats["total_executions_human_readable"] = format_decimals(mirrorr_stats["total_executions"], precision=1) or "0"

    if isinstance(duration, (int, float)) and duration > 0:
        mirrorr_stats["total_executions_duration"] = mirrorr_stats["total_executions_duration"] + duration if "total_executions_duration" in mirrorr_stats else duration
        mirrorr_stats["total_executions_duration_human_readable"] = format_duration(mirrorr_stats["total_executions_duration"], False)

    if isinstance(bytes_transferred, int) and bytes_transferred > 0:
        mirrorr_stats["total_bytes_transferred"] = mirrorr_stats["total_bytes_transferred"] + bytes_transferred if "total_bytes_transferred" in mirrorr_stats else bytes_transferred
        mirrorr_stats["total_bytes_transferred_human_readable"] = format_binaries(mirrorr_stats["total_bytes_transferred"])

    if status in ["SUCCESS", "NOOP", "PARTIAL_SUCCESS"]:
        mirrorr_stats["total_successes"] = mirrorr_stats["total_successes"] + 1 if "total_successes" in mirrorr_stats else 1
    else:
        mirrorr_stats["total_fails"] = mirrorr_stats["total_fails"] + 1 if "total_fails" in mirrorr_stats else 1

    if status == "NOOP":
        mirrorr_stats["total_noops"] = mirrorr_stats["total_noops"] + 1 if "total_noops" in mirrorr_stats else 1    

    if reporters_exit_code != 0:
        mirrorr_stats["total_reporters_fails"] = mirrorr_stats["total_reporters_fails"] + 1 if "total_reporters_fails" in mirrorr_stats else 1

    mirrorr_stats["last_job_name"] = MIRRORR_JOB['name']
    mirrorr_stats["last_job_exit_code"] = exit_code
    mirrorr_stats["last_reporters_exit_code"] = reporters_exit_code

    now = datetime.now()
    mirrorr_stats["last_updated_at"] = now.timestamp()
    mirrorr_stats["last_updated_at_human_readable"] = format_date(now)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Statistics updated, saving")    
    with open(mirrorr_stats_file, 'w') as f:
        yaml.dump(mirrorr_stats, stream=f, sort_keys=True)

    return mirrorr_stats