import logging
import re
import subprocess
from pathlib import Path
import yaml
import os


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
                path = Path(value)
                if not path.exists():
                    violations.append({label: "Path is not resolvable"})
                if not os.access(path, os.X_OK):
                    violations.append({label: "Path is not traversable"})

                # TODO somehow this doesn't seem to have an effect. It does work in mirrorr.py, but not here.
                if label == "Source" and not os.access(path, os.R_OK):
                    violations.append({label: "Path is not readable"})

                # TODO somehow this doesn't seem to have an effect. It does work in mirrorr.py, but not here.
                if label == "Destination" and not os.access(path, os.W_OK):
                    violations.append({label: "Path is not writable"})
            except PermissionError:
                violations.append({label: "Permission denied"})

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
    with open(conf_file_path, 'r') as f:
        return yaml.safe_load(f)


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


def enable_dryruns(job, enable:bool=True):
    job_path = job_file_path(job['name'])
    job['dryruns'] = enable

    with open(job_path, 'w') as f:
        yaml.dump(job, f)


def disable_dryruns(job):
    enable_dryruns(job, False)

