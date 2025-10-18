import logging
import subprocess
from pathlib import Path
import yaml
import os
import pwd
from utils import *

logger = logging.getLogger(__package__)

DATA_DIR = 'data'
JOBS_DIR = f'{DATA_DIR}/jobs'
JOBS_LOGS_DIR = f'{DATA_DIR}/logs'


def install_job(job):
    application_root = str(Path(".").resolve())
    job_conf_abspath = str((Path(JOBS_DIR) / f"{job['name']}.yaml").resolve())
    mirror_conf_abspath = str((Path(DATA_DIR) / "conf.yaml").resolve())

    stdout, stderr, exit_code = run_shell_script(
        'sys/install-unit.sh', [
            job['name'],
            job['schedule'],
            application_root,
            job_conf_abspath,
            mirror_conf_abspath,
            str(Path(JOBS_LOGS_DIR).resolve())])

    if exit_code != 0:
        logger.error("shell exec stdout=" + str(stdout))
        logger.error("shell exec stderr=" + str(stderr))
        logger.error("shell exec returncode=" + str(exit_code))
        raise Exception("Error:" + stderr)


def uninstall_job(job):
    stdout, stderr, exit_code = run_shell_script(
        'sys/uninstall-unit.sh', [job['name']])

    if exit_code != 0:
        raise Exception("Error:" + stderr)


def is_job_running(job) -> bool:
    args = ['--user', 'is-active', job['name'].replace(' ', '_')]

    stdout, stderr, exit_code = run_shell_script(
        'systemctl', args)

    # if exit_code != 0:
    #     raise Exception("Error:" + stderr)

    return stdout.strip() == "active" or stdout.strip() == "activating"


def is_job_enabled(job) -> bool:
    args = ['--user', 'is-enabled', get_timer_name(job)]

    stdout, stderr, exit_code = run_shell_script(
        'systemctl', args)

    # if exit_code != 0 or exit_code != 1:
    #    raise Exception("Error:" + stderr)

    return stdout.strip() == "enabled"


def enable_job(job, enable:bool=True):
    args = ['--user', 'enable' if enable else 'disable', '--now', get_timer_name(job)]

    stdout, stderr, exit_code = run_shell_script(
        'systemctl', args)

    if exit_code != 0:
        raise Exception("Error:" + stderr)

    stdout, stderr, exit_code = run_shell_script(
        'systemctl',
        ['--user', 'daemon-reexec'])
    if exit_code != 0:
        raise Exception("Error:" + stderr)


def disable_job(job):
    enable_job(job, False)


def kill_job(job):
    args = ['--user', 'stop' , get_service_name(job)]

    stdout, stderr, exit_code = run_shell_script(
        'systemctl', args)

    if exit_code != 0:
        raise Exception("Error:" + stderr)


def get_runtime(job) -> str:
    stdout, stderr, exit_code = run_shell_script(
        'systemctl',
        ['--user', 'show', get_timer_name(job), '-p', 'ActiveEnterTimestamp', '--value'])

    if exit_code != 0:
        raise Exception("Error:" + stderr)

    return calculate_duration_to_now(
        str(stdout).strip())

def get_last_ran(job) -> str:
    stdout, stderr, exit_code = run_shell_script(
        'systemctl',
        ['--user', 'show', get_timer_name(job), '-p', 'LastTriggerUSec', '--value'])

    if exit_code != 0:
        raise Exception("Error:" + stderr)

    return calculate_duration_to_now(
        str(stdout).strip(), False)


def run_shell_script(script, args: list):
    cmd = [script] + args
    logger.debug(str(cmd) + "  -->")

    env = os.environ.copy()
    uid = pwd.getpwnam("mirrorr").pw_uid
    env["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

    logger.debug("shell exec stdout=" + str(result.stdout))
    logger.debug("shell exec stderr=" + str(result.stderr))
    logger.debug("shell exec returncode=" + str(result.returncode))
    logger.debug("<-- \n")

    return result.stdout, result.stderr, result.returncode
