import logging
import time
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_fqdn_or_ip = None


def detect_fqdn_or_ip() -> str:
    global _fqdn_or_ip
    if _fqdn_or_ip:
        return _fqdn_or_ip

    fqdn = os.popen('hostname -f').read().strip()
    if not fqdn or '.' not in fqdn:
        result = os.popen('ip a s dev eth0').read()
        for line in result.splitlines():
            line = line.strip()
            if line.startswith('inet '):
                fqdn = line.split()[1].split('/')[0]
                break

    _fqdn_or_ip = fqdn or "localhost"
    return _fqdn_or_ip


def validate_job_required_fields(job: dict, violations: list):
    required_fields = ["name", "schedule", "source", "dest"]
    if job.get("rsync_delete"):
        required_fields.append("allowed_percentage")

    for field_name in required_fields:
        if field_name not in job or job.get(field_name) == "":
            violations.append({field_name: "This field is required"})


def validate_job_field_types(job: dict, violations: list):
    str_fields = ["name", "description", "schedule", "source", "rsync_exclude", "dest", "rsync_bwlimit", "rsync_nice", "rsync_ionice"]
    for field_name in str_fields:
        if field_name in job and not isinstance(job[field_name], str):
            violations.append({field_name: "This field must be a string"})

    int_fields = ["allowed_percentage"]
    for field_name in int_fields:
        if field_name in job and job[field_name] is not None and not isinstance(job[field_name], int):
            violations.append({field_name: "This field must be an integer"})

    bool_fields = ["remote_source", "remote_dest", "rsync_delete", "rsync_no_owner", "rsync_no_group", "rsync_no_perms", "rsync_acls", "rsync_no_times", "rsync_in_place", "rsync_whole_file", \
    "rsync_fsync", "rsync_verbose", "rsync_cvs_exclude", "reporter_o2", "reporter_discord", "report_noop", "log_noop", "report_success", "log_success", "debug", "enabled", "dryruns"]
    for field_name in bool_fields:
        if field_name in job and not isinstance(job[field_name], bool):
            violations.append({field_name: "This field must be a boolean"})


def validate_job_path(name: str, path: str, is_remote: bool, skip_path_existence_check: bool, violations: list):
    if re.search(r"\.\.", path):
        violations.append({name: "Must not contain '..'"})

    if is_remote != True:
        if re.search(r"[^A-Za-z0-9 ._/\-()\[\]#@,~\$]", path):
            violations.append({name: "Can only contain A-Za-z0-9 ._/-()[]#@,~$"})
        if not re.match(r"^/[^/ ].*", path):
            violations.append({name: "Must be absolute path and non empty (/ is invalid)"})
            return

        if not skip_path_existence_check:
            try:
                path = Path(path)
                if not path.exists():
                    violations.append({name: "Path is not resolvable"})
                if not os.access(path, os.X_OK):
                    violations.append({name: "Path is not traversable"})

                # TODO somehow this doesn't seem to have an effect. It does work in mirrorr.py, but not here.
                if name == "Source" and not os.access(path, os.R_OK):
                    violations.append({name: "Path is not readable"})

                # TODO somehow this doesn't seem to have an effect. It does work in mirrorr.py, but not here.
                if name == "Destination" and not os.access(path, os.W_OK):
                    violations.append({name: "Path is not writable"})
            except PermissionError:
                violations.append({name: "Permission denied"})
    else:
        if not re.search(r"^[^:@\s]+@[^:/\s]+:/\S+$", path):
            violations.append({name: "Not a valid scp address. Use this format: user@server:/folder/"})


def validate_allowed_percentage(allowed_percentage: int, job_deletes: bool, violations: list):
    allowed_percentage_err = {"allowed_percentage": "This must be a number between 1 and 100"}
    if allowed_percentage not in (None, ""):
        try:
            allowed_percentage = int(allowed_percentage)
            if allowed_percentage < 1 or allowed_percentage > 100:
                violations.append(allowed_percentage_err)
        except ValueError:
            violations.append(allowed_percentage_err)
    else:
        if job_deletes == True:
            violations.append({"allowed_percentage": "When a job is set to delete, this cannot be empty"})


def validate_settings_field_types(settings: dict, violations: list):
    str_fields = ["color_theme", "your_brand", "health_heartbeat_url", "server_address", "job_view_layout", "job_ordering"]
    for field_name in str_fields:
        if field_name in settings and not isinstance(settings[field_name], str):
            violations.append({field_name: "This field must be a string"})

    dict_fields = ["o2_reporter", "discord_reporter"]
    for field_name in dict_fields:
        if field_name in settings and not isinstance(settings[field_name], dict):
            violations.append({field_name: "This field must be a map"})

    if "o2_reporter" in settings:
        for field_name in ["o2_server_url", "o2_server_auth"]:
            if field_name in settings["o2_reporter"] and not isinstance(settings["o2_reporter"][field_name], str):
                violations.append({f"o2_reporter/{field_name}": "This field must be a string"})

    if "discord_reporter" in settings:
        for field_name in ["webhook_url", "template"]:
            if field_name in settings["discord_reporter"] and not isinstance(settings["discord_reporter"][field_name], str):
                violations.append({f"discord_reporter/{field_name}": "This field must be a string"})

    int_fields = ["scheduler_cycle_s", "ui_refresher_s", "log_retention_count", "remote_ssh_port"]
    for field_name in int_fields:
        if field_name in settings and settings[field_name] is not None and not isinstance(settings[field_name], int):
            violations.append({field_name: "This field must be an integer"})

    bool_fields = ["reverse_cron", "cool_timestamps"]
    for field_name in bool_fields:
        if field_name in settings and not isinstance(settings[field_name], bool):
            violations.append({field_name: "This field must be a boolean"})


def validate_settings_deny_unknown_fields(settings: dict, violations: list):
    for field in settings:
        if field not in ["color_theme", "reverse_cron", "cool_timestamps", "scheduler_cycle_s", "ui_refresher_s", "log_retention_count", "your_brand", \
            "o2_reporter", "discord_reporter", "health_heartbeat_url", "remote_ssh_port", "server_address", "job_view_layout", "job_ordering"]:
            violations.append({"general": f"Field {field} is unknown"})
    
    if "o2_reporter" in settings:
        for field in settings["o2_reporter"]:
            if field not in ["o2_server_url", "o2_server_auth"]:
                violations.append({"general": f"Field o2_reporter/{field} is unknown"})

    if "discord_reporter" in settings:
        for field in settings["discord_reporter"]:
            if field not in ["webhook_url", "template"]:
                violations.append({"general": f"Field discord_reporter/{field} is unknown"})


def validate_settings_field_values(settings: dict, violations: list):
    fields_and_values = {
        "color_theme": ["color-theme-green", "color-theme-mauve", "color-theme-blue", "color-theme-pastel", "color-theme-brown", "color-theme-denim", "color-theme-midnight", "color-theme-icegrey", "color-theme-inverted", "color-theme-monowhite"],
        "scheduler_cycle_s": [10, 60, 600],
        "ui_refresher_s": [5, 15, 60],
        "log_retention_count": [3, 10, 100],
        "job_ordering": ["name / asc", "name / desc", "last-run / asc", "last-run / desc", "next-run / asc", "next-run / desc"],
        "job_view_layout": ["listing", "grid"]
    }

    for field, allowed_values in fields_and_values.items():
        if field in settings and settings[field] not in allowed_values:
            allowed_values_str = ", ".join(map(str, allowed_values))
            violations.append({field: f"Invalid value. Allowed values: {allowed_values_str}"})

    if "remote_ssh_port" in settings:
        remote_ssh_port = settings["remote_ssh_port"]
        if remote_ssh_port is not None and (remote_ssh_port < 0 or remote_ssh_port > 65535):
            violations.append({"remote_ssh_port": f"Invalid value. Allowed values: range 0 - 65535"})
