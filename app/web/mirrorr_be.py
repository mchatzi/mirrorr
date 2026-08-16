import logging
import re
import threading
from pathlib import Path
import yaml
import os
import copy
from scheduler import update_cache_job, remove_cache_job, kill_job, refresh_scheduler_cycle
from utils import validate_job_path, validate_allowed_percentage, validate_job_field_types, validate_job_required_fields
from datetime import datetime
from croniter import croniter


logger = logging.getLogger(__name__)
SETTINGS_CACHE = {}
_SETTINGS_CACHE_LOCK = threading.Lock()

MIRRORR_ROOT_DIR = "../.."
DATA_DIR = f"{MIRRORR_ROOT_DIR}/data"
JOBS_DIR = f"{DATA_DIR}/jobs"
JOBS_LOGS_DIR = f"{DATA_DIR}/logs"


def ensure_defaults(settings: dict) -> dict:     
    if 'color_theme' not in settings:
        settings['color_theme'] = 'color-theme-green'
    if 'scheduler_cycle_s' not in settings:
        settings['scheduler_cycle_s'] = 60
    if 'ui_refresher_s' not in settings:
        settings['ui_refresher_s'] = 5
    if 'log_retention_count' not in settings:
        settings['log_retention_count'] = 10

    return settings


def job_file_path(name):
    return Path(JOBS_DIR) / f"{name}.yaml"


def validate_job(job:dict, skip_path_existence_check:bool = False):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Validating job: {job.get('name', 'unknown')}")

    violations = []

    validate_job_required_fields(job, violations)
    if violations:
        return violations

    validate_job_field_types(job, violations)
    if violations:
        return violations

    if re.search(r"[^A-Za-z0-9 ._]", job['name']):
        violations.append({"name": "Can only contain [A-Za-z0-9 ._]"})

    validate_job_path("source", job['source'], job.get("remote_source"), skip_path_existence_check, violations)
    validate_job_path("dest", job['dest'], job.get("remote_dest"), skip_path_existence_check, violations)
    validate_allowed_percentage(job.get("allowed_percentage"), job.get("rsync_delete"), violations)
    
    try:
        #croniter.is_valid(job['schedule'])
        croniter(job['schedule'], datetime.now())
    except Exception as e:
        violations.append({"schedule": str(e)})

    return violations if violations else []


def load_jobs() -> list:
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Loading all jobs from disk")

    jobs = []
    jobsDir = Path(JOBS_DIR)
    if jobsDir.exists():
        for file in jobsDir.iterdir():
            if file.name.endswith(".yaml"):
                with open(Path(JOBS_DIR) / file.name, 'r') as f:
                    job = yaml.safe_load(f)
                    jobs.append(job)
    return jobs

def load_job(name: str) -> dict:
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loading job {name} from disk")

    job = None
    jobsDir = Path(JOBS_DIR)
    if jobsDir.exists():
        for file in jobsDir.iterdir():
            if file.name == f"{name}.yaml":
                with open(Path(JOBS_DIR) / file.name, 'r') as f:
                    job = yaml.safe_load(f)
    return job

def save(job):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Saving job: {job['name']}")

    with open(job_file_path(job['name']), 'w') as f:
        yaml.dump(job, f)
    
    update_cache_job(job['name'], job)


def delete(name):
    if logger.isEnabledFor(logging.DEBUG):
        logger.info(f"Deleting job: {name}")

    stop(name)
    remove_cache_job(name)

    path = job_file_path(name)
    if path.exists():
        path.unlink()

    purge_job_logs(name)


def stop(name):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Stopping job: {name}")

    kill_job(name)

def enable(job, enable: bool = True):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Setting job {job['name']} enabled={enable}")

    job['enabled'] = enable
    save(job)


def disable(job):
    enable(job, False)


def enable_dryruns(job, enable:bool=True):
    job['dryruns'] = enable
    save(job)


def disable_dryruns(job):
    enable_dryruns(job, False)


def purge_job_logs(name):
    pattern = re.compile(rf"^{re.escape(name)}(?:\.\d+)?\.log$")
    [file.unlink() for file in Path(JOBS_LOGS_DIR).iterdir() if pattern.match(file.name)]


def load_settings() -> dict:
    global SETTINGS_CACHE
    with _SETTINGS_CACHE_LOCK:
        if SETTINGS_CACHE is None or not SETTINGS_CACHE:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Loading settings from disk")
            conf_file_path = f"{DATA_DIR}/conf.yaml"
            with open(conf_file_path, 'r') as f:
                SETTINGS_CACHE = yaml.safe_load(f) or {}

        return copy.deepcopy(SETTINGS_CACHE)


def save_settings(settings):
    settings_copy = copy.deepcopy(settings)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Saving settings to disk")
    conf_file_path = f"{DATA_DIR}/conf.yaml"
    with open(conf_file_path, 'w') as f:
        yaml.dump(settings_copy, stream=f, sort_keys=False)

    global SETTINGS_CACHE
    do_refresh = False
    with _SETTINGS_CACHE_LOCK:
        if SETTINGS_CACHE.get("scheduler_cycle_s") != settings_copy.get("scheduler_cycle_s"):
            do_refresh = True
        SETTINGS_CACHE = settings_copy

    if do_refresh:
        refresh_scheduler_cycle()


def get_all_log_indices(name) -> list:
    all_logs = []

    for file in Path(JOBS_LOGS_DIR).iterdir():
        if file.name == f"{name}.log":
            all_logs.append(0)
        elif file.name.startswith(name):
            log_index = re.findall(rf"(?:{name}\.)(\d*)(?:\.log)", file.name)
            if log_index:
                all_logs.append(int(log_index[0]))

    all_logs.sort()
    return all_logs


def get_log(name, index):
    log_path = Path(f"{JOBS_LOGS_DIR}/{name}." + (str(index) + "." if index else "") + "log")

    if log_path.exists():
        file_size = log_path.stat().st_size
        if file_size > 0.5 * 1024 ** 2:
            return {"too_big": f"{file_size / (1024 ** 2):.2f}MB"}
        else:
            with open(log_path, "r") as log:
                return {"content": log.read()}
    else:
        return False

