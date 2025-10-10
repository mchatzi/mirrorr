import logging
import re
import subprocess
from pathlib import Path
import yaml
import os
import pwd


logger = logging.getLogger(__package__)

DATA_DIR = 'data'
JOBS_DIR = f'{DATA_DIR}/jobs'
JOBS_LOGS_DIR = f'{DATA_DIR}/logs'


def job_file_path(name):
    return Path(JOBS_DIR) / f"{name}.yaml"


def validate_job(job:dict, skip_path_existence_check:bool = False):
    violations = []

    if re.search(r"[^A-Za-z0-9 ._]", job['name']):
        violations.append({"name": "Can only contain [A-Za-z0-9 ._]"})

    path_inputs = [("source", job['source']), ("dest", job['dest'])]
    path_violations = []
    path_violations.extend([{label: "Can only contain A-Za-z0-9 ._/-()[]#@,~$"} for label, value in path_inputs if re.search(r"[^A-Za-z0-9 ._/\-()\[\]#@,~\$]", value)])
    path_violations.extend([{label: "Must be absolute path and non empty (/ is invalid)"} for label, value in path_inputs if not re.match(r"^/[^/ ].*", value)])
    path_violations.extend([{label: "Must not contain '..'"} for label, value in path_inputs if re.search(r"\.\.", value)])
    violations.extend(path_violations)

    if not skip_path_existence_check and not path_violations:
        for label, value in path_inputs:
            try:
                if not Path(value).exists():
                    violations.append({label: "Path is not resolvable"})
            except PermissionError:
                violations.append({label: "Permission denied"})

    # TODO Allows /../ currently


    allowed_percentage = job['allowed_percentage']
    if allowed_percentage < 0 or allowed_percentage > 100:
        violations.append({"allowed_percentage": "Must be between 0 and 100"})

    return violations if violations else []


def load_jobs() -> list:
    jobs = []
    jobsDir = Path(JOBS_DIR)
    if jobsDir.exists():
        for file in jobsDir.iterdir():
            if file.name.endswith(".yaml"):
                with open(Path(JOBS_DIR) / file.name, 'r') as f:
                    job = yaml.safe_load(f)
                    jobs.append(job)

    [job.update({'logfile': True}) for job in jobs
     if Path(f"{JOBS_LOGS_DIR}/{job['name']}.log").exists()]

    return jobs


def save_job(job):
    with open(job_file_path(job['name']), 'w') as f:
        yaml.dump(job, f)


def delete_job_files(name):
    path = job_file_path(name)
    if path.exists():
        path.unlink()

    purge_job_logs(name)


def purge_job_logs(name):
    [file.unlink() for file in Path(JOBS_LOGS_DIR).iterdir() if file.name.startswith(name)]


def load_settings() -> dict:
    conf_file_path = Path("data/conf.yaml")
    if conf_file_path.exists():
        with open(conf_file_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {
            # TODO More defaults
            "color_theme": "color-theme-green"
        };


def save_settings(settings):
    conf_file_path = "data/conf.yaml"
    with open(conf_file_path, 'w') as f:
        yaml.dump(settings, stream=f, sort_keys=False)


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
        if file_size > 5 * 1024 ** 2:
            return {"too_big": f"{file_size / (1024 ** 2):.2f}MB"}
        else:
            with open(log_path, "r") as log:
                return {"content": log.read()}
    else:
        return False


def install_job(job):
    application_root = str(Path(".").resolve())
    job_conf_abspath = str((Path(JOBS_DIR) / f"{job['name']}.yaml").resolve())
    mirror_conf_abspath = str((Path(DATA_DIR) / "conf.yaml").resolve())
    group = load_settings().get("group", "")

    stdout, stderr, exit_code = run_shell_script(
        'sys/install-unit.sh', [
            job['name'],
            job['schedule'],
            application_root,
            job_conf_abspath,
            mirror_conf_abspath,
            "DEBUG",
            # ip but it's now retrieved in the sh,
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


def enable_dryruns(job, enable:bool=True):
    job_path = job_file_path(job['name'])
    job['dryruns'] = enable

    with open(job_path, 'w') as f:
        yaml.dump(job, f)


def disable_dryruns(job):
    enable_dryruns(job, False)


def get_timer_name(job) -> str:
    return job['name'].replace(' ', '_') + ".timer"


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
