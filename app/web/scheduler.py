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

logger = logging.getLogger(__name__)

MIRRORR_ROOT_DIR = '../..'
DATA_DIR = f'{MIRRORR_ROOT_DIR}/data'
JOBS_DIR = f'{DATA_DIR}/jobs'
JOBS_LOGS_DIR = f'{DATA_DIR}/logs'

TICK_SECONDS = 60

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

    logger.info(f"Have set the scheduler cycle to {TICK_SECONDS} seconds")



def _run_scheduler():
    if logger.isEnabledFor(logging.DEBUG):
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

                logger.info("Checking job schedules...")
                if logger.isEnabledFor(logging.DEBUG):
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

        logger.info(f"Starting job thread for: {job_name}")
        thread = threading.Thread(
            target=run_job,
            args=[job_name],
            daemon=True
        )
        started_at = time.time()
        _set_running(job_name, started_at)
        thread.start()
    except Exception as e:
        if _get_job_execution(job_name).get('status') == 'running':
            _set_idle(job_name)
        logger.error(f"Error starting job thread for job '{job_name}': {e}")
    finally:
        _launch_lock.release()


def run_job(job_name: str):
    from mirrorr_be import save, job_file_path, load_job
    try:
        application_root = str(Path(MIRRORR_ROOT_DIR).resolve())
        fqdn_or_ip = detect_fqdn_or_ip()
        argv = [
            f'{application_root}/app/sys/.venv/bin/python',
            f'{application_root}/app/sys/mirrorr.py',
            '-conf', str(Path(DATA_DIR).resolve() / "conf.yaml"),
            '-job', str(job_file_path(job_name).resolve()),
            '-fqdn_or_ip', fqdn_or_ip,
            '-logsdir', str(Path(JOBS_LOGS_DIR).resolve()),
            '-app_log_level', logging.getLevelName(logger.getEffectiveLevel())
        ]

        process = subprocess.Popen(argv, cwd=application_root)
        _set_process(job_name, process)
        logger.info(f"Job thread started for: {job_name}")
        process.wait()
        logger.info(f"Job {job_name} completed with exit code {process.returncode}")

    except Exception as e:
        logger.error(f"Error running job '{job_name}': {e}")
    finally:
        logger.info(f"Job {job_name} cleanup: setting to idle")
        _set_idle(job_name)

        #Re-read the job as schedules may have changed, job may have been disabled etc
        latest_job = load_job(job_name)
        if latest_job:
            latest_job['last_run'] = time.time()
            save(latest_job)


def _set_idle(job_name: str):
    with _cache_lock:
        _job_executions[job_name]['status'] = 'idle'
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Job {job_name} set to idle status")


def _set_next_run(job_name: str, next_run: datetime):
    with _cache_lock:
        _job_executions[job_name]['next_run'] = next_run
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Job {job_name} next_run set to {next_run}")


def _set_queued(job_name: str):
    with _cache_lock:
        _job_executions[job_name]['status'] = 'queued'
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Job {job_name} set to queued status")


def _set_running(job_name: str, started_at: float):
    with _cache_lock:
        job_execution = _job_executions[job_name]
        job_execution['status'] = 'running'
        job_execution['started_at'] = started_at
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Job {job_name} set to running status")


def _set_process(job_name: str, process: subprocess.Popen):
    with _cache_lock:
        job_execution = _job_executions[job_name]
        job_execution['process'] = process
    if logger.isEnabledFor(logging.DEBUG):
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
    if logger.isEnabledFor(logging.DEBUG):
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








