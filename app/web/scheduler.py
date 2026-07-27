import logging
import os
import subprocess
import threading
import time
import pprint
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from croniter import croniter
from utils import *

logger = logging.getLogger(__package__)

DATA_DIR = 'data'
JOBS_DIR = f'{DATA_DIR}/jobs'
JOBS_LOGS_DIR = f'{DATA_DIR}/logs'

TICK_SECONDS = 60

_job_executions = {}
_job_executions = {}
_cache_lock = threading.Lock()
_executions_lock = threading.Lock()
_launch_lock = threading.Lock()
wake_up_event = threading.Event()



def start_scheduler():
    from mirrorr_be import load_settings
    logger.info("Starting Scheduler..")

    if wake_up_event.is_set():
        wake_up_event.clear()

    _init_job_executions()
    thread = threading.Thread(target=_run_scheduler, daemon=True)
    thread.start()


def refresh_scheduler_cycle(wake_up_thread: bool = True):
    from mirrorr_be import load_settings
    global TICK_SECONDS

    TICK_SECONDS = int(load_settings().get('scheduler_cycle_s'))
    if wake_up_thread:
        wake_up_event.set()

    logger.debug(f"Have set the scheduler cycle to {TICK_SECONDS} seconds")



def _run_scheduler():
    logger.debug("Scheduler thread started, entering event loop")
    is_woken_up = False

    while True:
        if is_woken_up:
            wake_up_event.clear()
        else:
            try:
                now = datetime.now()
                with _cache_lock:
                    job_executions= list(_job_executions.items())

                #Order by next_run -> so the oldest queued job gets to go first
                job_executions.sort(key=lambda job_execution_tuple: job_execution_tuple[1].get("next_run")
                    if job_execution_tuple[1] and job_execution_tuple[1].get("next_run") is not None else datetime.max)

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("#############    Checking job schedules...     #############")
                    logger.debug(f"Current executions:\n{pprint.pformat(job_executions, indent=4)}")

                for job_name, job_execution in job_executions:
                    next_run = job_execution.get('next_run')

                    if next_run is None or now < next_run:
                        continue

                    if job_execution.get('status') == 'running':
                        continue

                    logger.info(f"Launching job: {job_name}")
                    try:
                        launch_job(job_execution['data'])
                    except Exception as e:
                        logger.error(f"Error launching job '{job_name}': {e}")

            except Exception as e:
                logger.error(f"Scheduler tick failed: {e}")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"I can finally sleep for {TICK_SECONDS} seconds")

        is_woken_up = wake_up_event.wait(timeout=TICK_SECONDS)


def launch_job(job):
    from mirrorr_be import load_settings
    job_name = job['name']

    if not _launch_lock.acquire(blocking=False):
        logger.info(f"Job {job_name} queued (lock held by another job)")
        _set_queued(job_name)
        return

    try:
        if _another_job_is_running():
            logger.info(f"Job {job_name} queued (another job is running)")
            _set_queued(job_name)
            return

        job_copy = deepcopy(job)
        conf_copy = deepcopy(load_settings())
        logs_dir_abspath = str(Path(JOBS_LOGS_DIR).resolve())

        started_at = time.time()
        _set_running(job_name, started_at)

        thread = threading.Thread(
            target=_run_job_thread,
            args=(job_name, job_copy, conf_copy, detect_fqdn_or_ip(), logs_dir_abspath),
            daemon=True
        )
        logger.info(f"Starting job thread for: {job_name}")
        thread.start()
    finally:
        _launch_lock.release()


def _run_job_thread(job_name: str, job_copy, conf_copy, fqdn_or_ip, logs_dir):
    from mirrorr_be import save, job_file_path, load_jobs
    try:
        application_root = str(Path(".").resolve())
        argv = [
            f'{application_root}/app/sys/.venv/bin/python',
            f'{application_root}/app/sys/mirrorr.py',
            '-conf', str(Path(DATA_DIR).resolve() / "conf.yaml"),
            '-job', str(job_file_path(job_name).resolve()),
            '-fqdn_or_ip', fqdn_or_ip,
            '-logsdir', logs_dir,
        ]

        process = subprocess.Popen(argv, cwd=application_root)
        _set_process(job_name, process)
        logger.info(f"Job thread started for: {job_name}")
        process.wait()
        logger.info(f"Job {job_name} completed with exit code {process.returncode}")

    except Exception as e:
        logger.error(f"Error running job '{job_name}': {e}")
    finally:
        logger.debug(f"Job {job_name} cleanup: setting to idle")

        #Re-read the job as schedules may have changed, job may have been disabled etc
        latest_job = next((j for j in load_jobs() if j['name'] == job_name), None)
        if latest_job:
            latest_job['last_run'] = time.time()
            save(latest_job)
            _set_idle(job_name)


def _set_idle(job_name: str):
    with _cache_lock:
        _job_executions[job_name]['status'] = 'idle'
    logger.debug(f"Job {job_name} set to idle status")


def _set_next_run(job_name: str, next_run: datetime):
    with _cache_lock:
        _job_executions[job_name]['next_run'] = next_run
    logger.debug(f"Job {job_name} next_run set to {next_run}")


def _set_queued(job_name: str):
    with _cache_lock:
        _job_executions[job_name]['status'] = 'queued'
    logger.debug(f"Job {job_name} set to queued status")


def _set_running(job_name: str, started_at: float):
    with _cache_lock:
        job_execution = _job_executions[job_name]
        job_execution['status'] = 'running'
        job_execution['started_at'] = started_at
    logger.debug(f"Job {job_name} set to running status")


def _set_process(job_name: str, process: subprocess.Popen):
    with _cache_lock:
        job_execution = _job_executions[job_name]
        job_execution['process'] = process
    logger.debug(f"Set execution process for {job_name} (PID: {process.pid})")


def _get_job_execution(job_name: str) -> dict:
    with _cache_lock:
        return _job_executions[job_name]


def _another_job_is_running() -> str:
    with _cache_lock:
        for _, info in _job_executions.items():
            if info.get('status') == 'running':
                return True
        return False

def _compute_next_run(job) -> datetime:
    logger.debug(f"Computing next run for job {job['name']}")
    if not job.get('enabled'):
        return None

    schedule_expr = job['schedule']
    now = datetime.now()
    cron = croniter(schedule_expr, now)

    # Catch up in case a job didn't run when it should have
    last_run = job.get('last_run')
    if last_run is not None:
        last_run_dt = datetime.fromtimestamp(last_run)
        last_run_according_to_cron = cron.get_prev(datetime)
        if last_run_according_to_cron > last_run_dt:
            return last_run_according_to_cron
        # Reset the iterator internal anchor back to 'now' if catch-up conditions didn't meet
        cron.set_current(now)

    # Calculate the next calendar occurrence
    next_run = cron.get_next(datetime)
    return next_run


################## API Methods #################

def get_job_execution(job_name: str) -> dict:
    with _cache_lock:
        job_execution = _job_executions.get(job_name, {})
        job_execution_info = {
            'status': job_execution.get('status', 'idle'),
        }

        if job_execution.get('data') and job_execution.get('data').get('last_run'):
            job_execution_info['last_run'] = job_execution['data']['last_run']

        if job_execution.get('status') == 'running' and job_execution.get('started_at'):
            job_execution_info['started_at'] = job_execution['started_at']

        if job_execution.get('next_run'):
            job_execution_info['next_run'] = job_execution['next_run'].timestamp()

        return job_execution_info


def kill_job(job_name):
    logger.info(f"Killing job {job_name}")
    job_execution = _get_job_execution(job_name)

    if job_execution.get('status') != 'running':
        logger.info(f"Job {job_name} is not running")
        return

    try:
        job_execution['process'].terminate()
        logger.info(f"Job {job_name} killed")
    except (ProcessLookupError, AttributeError):
        pass

    _set_idle(job_name)




############  MGMT METHODS ################

def _init_job_executions():
    from mirrorr_be import load_jobs
    logger.info("Initializing job execution cache from disk")
    with _cache_lock:
        _job_executions.clear()
        jobs = load_jobs()
        for job in jobs:
            _job_executions[job['name']] = {
                'data': job,
                'next_run': _compute_next_run(job)
            }
        logger.info(f"Cache initialized with {len(jobs)} jobs")


def update_cache_job(job_name: str, job):
    logger.info(f"Updating execution cache for job: {job_name}")
    with _cache_lock:
        _job_executions.setdefault(job_name, {})
        _job_executions[job_name]['data'] = job
        _job_executions[job_name]['next_run'] = _compute_next_run(job)


def remove_cache_job(job_name: str):
    logger.info(f"Removing from execution cache: {job_name}")
    with _cache_lock:
        _job_executions.pop(job_name, None)








