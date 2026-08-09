#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
import yaml
import pprint
import report
import utils

SUCCESS = "SUCCESS"
PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
NOOP = "NOOP"
ABORTED = "ABORTED"
FAILED = "FAILED"
UNKNOWN = "UNKNOWN"

WEB_LOGS_URL = ""

MIRRORR_JOB = {}
MIRRORR_CONF = {}

report.MIRRORR_JOB = MIRRORR_JOB
utils.MIRRORR_JOB = MIRRORR_JOB
report.MIRRORR_CONF = MIRRORR_CONF

logger = logging.getLogger("mirrorr")



def main():
    report.send_heartbeat()
    begin = time.time()

    violations = utils.validate_paths()
    if violations:
        job_finished(FAILED, 1, stderr='\n'.join(violations), started_at=begin)

    stats = {}
    stdout = None
    exit_code = None
    stderr = None

    # DRY
    if MIRRORR_JOB['dryruns'] == True or \
        (MIRRORR_JOB['rsync_delete'] == True and MIRRORR_JOB['allowed_percentage'] < 100):

        logger.debug(f"Running dry run for {MIRRORR_JOB['name']}")
        stdout, exit_code, stderr = run_rsync(dry_run=True)
        if exit_code not in (0, 23, 24):
            job_finished(FAILED, exit_code=exit_code, stderr=stderr, started_at=begin)

        stats = utils.parse_rsync_stats(stdout)
        if stats is None:
            job_finished(UNKNOWN, exit_code=exit_code, stderr=stderr, stdout=f"Unparseable rsync logs, job may have succeeded\n {stdout}", started_at=begin)
        
        do_percentage_check(stats, begin)

    # WET
    if not MIRRORR_JOB['dryruns']:
        logger.debug(f"Running wet run for {MIRRORR_JOB['name']}")
        stdout, exit_code, stderr = run_rsync(dry_run=False)
        

    # DONE, REPORT
    if exit_code in (0, 23, 24):
        stats = utils.parse_rsync_stats(stdout)
        if stats is None:
            job_finished(UNKNOWN, exit_code=exit_code, stderr=stderr, stdout=f"Unparseable rsync logs, job may have succeeded\n {stdout}", started_at=begin)

    if exit_code == 0:
        if stats['transferred'] + stats['deleted'] == 0:
            job_finished(NOOP, 0, stats=stats, started_at=begin)
        job_finished(SUCCESS, 0, stdout=stdout, stats=stats, started_at=begin)
    elif exit_code in (23,24):
        job_finished(PARTIAL_SUCCESS, exit_code, stderr=stderr, stdout=stdout, stats=stats, started_at=begin)
    else:
        job_finished(FAILED, exit_code=exit_code, stderr=stderr, stdout=stdout, started_at=begin)



def run_rsync(dry_run: bool = True) -> (str, int, str):
    command = []

    if MIRRORR_JOB['rsync_nice']:
        command += ["nice", "-n", str(MIRRORR_JOB['rsync_nice'])]
    if MIRRORR_JOB['rsync_ionice']:
        command += ["ionice", str(MIRRORR_JOB['rsync_ionice'])]

    command += ["rsync", "--recursive", "--links", "--info=stats2"]

    command.append("--no-owner" if MIRRORR_JOB["rsync_no_owner"] else "--owner")
    command.append("--no-group" if MIRRORR_JOB["rsync_no_group"] else "--group")
    command.append("--no-perms" if MIRRORR_JOB["rsync_no_perms"] else "--perms")
    command.append("--no-times" if MIRRORR_JOB["rsync_no_times"] else "--times")

    if MIRRORR_JOB['rsync_acls']:
        command.append("--acls")
    if MIRRORR_JOB['rsync_delete']:
        command.append("--delete")
    if MIRRORR_JOB['rsync_in_place']:
        command.append("--inplace")
    if MIRRORR_JOB['rsync_whole_file']:
        command.append("--whole-file")
    if MIRRORR_JOB['rsync_fsync']:
        command.append("--fsync")
    if MIRRORR_JOB['rsync_bwlimit']:
        command.append(f"--bwlimit={str(MIRRORR_JOB['rsync_bwlimit'])}")
    if dry_run:
        command.append("--dry-run")

    if MIRRORR_JOB.get('remote_source') == True or MIRRORR_JOB.get('remote_dest') == True:
        remote_ssh_port = 22;
        if not MIRRORR_CONF.get('remote_ssh_port'):
            logger.warning(f"Remote ssh port not configured, using default ({remote_ssh_port})")
        else:
            remote_ssh_port = str(MIRRORR_CONF['remote_ssh_port'])

        command += ["-e", f"ssh -i /opt/mirrorr/data/ssh/id_ed25519 -p {remote_ssh_port} -o UserKnownHostsFile=/opt/mirrorr/data/ssh/known_hosts"]

    command += [MIRRORR_JOB['source'], MIRRORR_JOB['dest']]

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Will execute rsync command for {MIRRORR_JOB['name']}:")
        logger.debug(repr(command))

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"EXITCODE ----------->{result.returncode}<----------")
            logger.debug(f"STDOUT ----------->\n{result.stdout}<----------/////STDOUT")
            logger.debug(f"STDERR ----------->\n{result.stderr}<----------/////STDERR")

        return result.stdout, result.returncode, result.stderr
    except Exception as e:
        exc_msg = f"{e}"
        logger.error(f"Error! {exc_msg}")
        return "", 1, exc_msg


def do_percentage_check(stats: dict, begin_time: float):
    if MIRRORR_JOB['rsync_delete'] is not True or MIRRORR_JOB['allowed_percentage'] == 100:
        logger.debug("Allowed percetange check skipped")
        return

    total_files_before = stats['total_files'] + stats['deleted']
    if total_files_before != 0:
        percentage_of_deleted = stats['deleted'] * 100 // total_files_before
        if percentage_of_deleted >= MIRRORR_JOB['allowed_percentage']:
            message = f"Too many files would be deleted ({percentage_of_deleted}%). Max allowed is {MIRRORR_JOB['allowed_percentage']}%"
            job_finished(ABORTED, 1, stderr=message, stats=stats, started_at=begin_time)

        


def job_finished(status:str, exit_code:int, started_at:int, stderr:str = "", stdout:str = "", stats: dict = {}):
    stats |= {'logfile_url': WEB_LOGS_URL + urllib.parse.quote(MIRRORR_JOB['name'])}

    duration = int(time.time() - started_at)
    stats |= {'duration': duration}
    stats |= {'human_readable_duration': utils.format_duration(duration)}
    stats |= {'human_readable_bytes_transferred': utils.format_bytes(stats.get('bytes_transferred', 0))}

    status_label = f'{status}{" -- DRY RUN" if MIRRORR_JOB["dryruns"] else ""}'
    logger.debug(f"Run completed for {MIRRORR_JOB['name']} with status label: {status_label}\nStats:\n{pprint.pformat(stats, indent=4)}")
    logger.debug("Updating logs and reporters...")

    if status in [FAILED, ABORTED]:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\nExit code: {exit_code}\n\n{stderr}")
        report.report(status_label, exit_code, message=stderr, stats=stats)
        sys.exit(1)
    elif status == UNKNOWN:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nExit code: {exit_code}\n\n{stdout}")
        report.report(status_label, exit_code, stats=stats, message="Unparseable rsync logs, job may have succeeded")
        sys.exit(0)
    elif status == NOOP:
        if MIRRORR_JOB['log_noop']:
            report.write_job_log(f"{status_label}\n\nNothing was transferred or deleted\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\nExit code: {exit_code}")
        if MIRRORR_JOB['report_noop']:
            report.report(status_label, exit_code, message="Nothing was transferred or deleted", stats=stats)
        sys.exit(0)
    elif status == SUCCESS:
        if MIRRORR_JOB['log_success']:
            report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\nExit code: {exit_code}\n\n{stdout}")
        if MIRRORR_JOB['report_success']:
            report.report(status_label, exit_code, message="All went well", stats=stats)
        sys.exit(0)
    elif status == PARTIAL_SUCCESS:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\n{stderr}\nExit code: {exit_code}\n\n{stdout}")
        # Don't send whole stderr, the last line contains what happened
        summary = (lambda lines: lines[-1] if lines else "")(str(stderr).splitlines())
        report.report(status_label, exit_code, stats=stats, message=summary)
        sys.exit(0)

    sys.exit(1)



def create_mirrorr_conf(args):
    global MIRRORR_CONF
    global WEB_LOGS_URL
    logger.debug("Loading global config")

    mirrorr_conf = Path(args.conf)
    if not mirrorr_conf.exists():
        logger.error(f"File {mirrorr_conf.name} not found")
        sys.exit(1)

    with open(mirrorr_conf, 'r') as f:
        MIRRORR_CONF.update(yaml.safe_load(f))

    if not MIRRORR_CONF.get('server_address'):
        logger.info(f"Server address is not configured, auto-detected: {args.fqdn_or_ip}")
        WEB_LOGS_URL = f"http://{args.fqdn_or_ip}:5000/joblog.html?name="  
    else:
        WEB_LOGS_URL = f"{MIRRORR_CONF['server_address']}/joblog.html?name="

    MIRRORR_CONF['job_logs_dir'] = args.logsdir

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loaded global config:\n{pprint.pformat(MIRRORR_CONF, indent=4)}")


def create_mirrorr_job(args):
    global MIRRORR_JOB

    job_conf = Path(args.job)
    if not job_conf.exists():
        logger.error(f"File {job_conf.name} not found")
        sys.exit(1)

    with open(job_conf, 'r') as f:
        MIRRORR_JOB.update(yaml.safe_load(f))

    if 'debug' in MIRRORR_JOB and MIRRORR_JOB['debug'] == True:
        logger.setLevel("DEBUG")

    if MIRRORR_JOB["rsync_delete"] == True:
        allowed_percentage = MIRRORR_JOB.get("allowed_percentage")

        if allowed_percentage in (None, ""):
            raise ValueError("This job is set to delete, but the allowed percentage is empty")

        try:
            allowed_percentage = int(allowed_percentage)
        except ValueError as e:
            raise e

        if allowed_percentage < 0 or allowed_percentage > 100:
            raise ValueError("This job is set to delete, but the allowed percentage is not between 0 and 100")

        MIRRORR_JOB["allowed_percentage"] = allowed_percentage


    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loaded job {args.job}:\n{pprint.pformat(MIRRORR_JOB, indent=4)}")


def setup_logging(args):
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d, %H:%M:%S')
    logger.setLevel(args.app_log_level)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the logging level")
    parser.add_argument('-conf', help='Absolute path to mirrorr conf file', required=True)
    parser.add_argument('-job', help='Absolute path to job conf file', required=True)
    parser.add_argument('-fqdn_or_ip', help='Fully qualified domain name or IP of the mirrorr web server', required=True)
    parser.add_argument('-logsdir', help='Dir where the job logs should go', required=True)
    parser.add_argument('-app_log_level', help='The application log level, unless job overrides this, mirrorr will use the app log level', required=True)

    args = parser.parse_args()

    setup_logging(args)
    logger.info("Mirrorr is starting the execution of a job")

    create_mirrorr_job(args)
    logger.info(f"Job loaded: {MIRRORR_JOB.get('name', 'error!')}")

    create_mirrorr_conf(args)

    main()
