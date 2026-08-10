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
import sys
import signal

SUCCESS = "SUCCESS"
PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
NOOP = "NOOP"
INVALID = "INVALID"
FAILED = "FAILED"
UNKNOWN = "UNKNOWN"
KILLED = "KILLED"
ABORTED = "ABORTED"

WEB_LOGS_URL = ""

MIRRORR_JOB = {}
MIRRORR_CONF = {}

report.MIRRORR_JOB = MIRRORR_JOB
report.MIRRORR_CONF = MIRRORR_CONF
utils.MIRRORR_JOB = MIRRORR_JOB
utils.MIRRORR_CONF = MIRRORR_CONF

logger = logging.getLogger("mirrorr")

rsync_process = None
shutdown_triggered = False


def main():
    ''' Main job workflow '''
    report.send_heartbeat()
    begin = time.time()

    violations = utils.validate_paths()
    if violations:
        job_finished(FAILED, 1, stderr_str='\n'.join(violations), started_at=begin)

    stats = {}
    exit_code = None
    getstdout = lambda: report.fully_load_log(report.get_temp_job_out_log_path())
    getstderr = lambda: report.fully_load_log(report.get_temp_job_err_log_path())

    # DRY RUN
    if MIRRORR_JOB['dryruns'] == True or \
        (MIRRORR_JOB['rsync_delete'] == True and MIRRORR_JOB['allowed_percentage'] < 100):

        logger.debug(f"Running dry run for {MIRRORR_JOB['name']}")
        exit_code, exc_msg = run_rsync(dry_run=True)
        if exc_msg:
            job_finished(FAILED, exit_code=exit_code, stderr_str=exc_msg, started_at=begin)
        if exit_code == 20:
            job_finished(KILLED, exit_code, stderr_str=getstderr(), stdout_str=getstdout(), stats=stats, started_at=begin)
        if exit_code not in (0, 23, 24):
            job_finished(FAILED, exit_code=exit_code, stderr_str=getstderr(), started_at=begin)

        stats = utils.parse_rsync_stats(getstdout())
        if stats is None:
            job_finished(UNKNOWN, exit_code=exit_code, stderr_str=getstderr(), stdout_str=f"Unparseable rsync logs, job may have succeeded\n {getstdout()}", started_at=begin)
        do_percentage_check(stats, begin)

    # WET RUN
    if not MIRRORR_JOB['dryruns']:
        logger.debug(f"Running wet run for {MIRRORR_JOB['name']}")
        exit_code, exc_msg = run_rsync(dry_run=False)
        if exc_msg:
            job_finished(FAILED, exit_code=exit_code, stderr_str=exc_msg, started_at=begin)

    # DONE, REPORT
    if exit_code in (0, 23, 24):
        stats = utils.parse_rsync_stats(getstdout())
        if stats is None:
            job_finished(UNKNOWN, exit_code=exit_code, stderr_str=getstderr(), stdout_str=f"Unparseable rsync logs, job may have succeeded\n {getstdout()}", started_at=begin)
    if exit_code == 20:
        job_finished(KILLED, exit_code, stderr_str=getstderr(), stdout_str=getstdout(), stats=stats, started_at=begin)
    if exit_code == 0:
        if stats['transferred'] + stats['deleted'] == 0:
            job_finished(NOOP, 0, stats=stats, started_at=begin)
        job_finished(SUCCESS, 0, stdout_str=getstdout(), stats=stats, started_at=begin)
    if exit_code in (23,24):
        job_finished(PARTIAL_SUCCESS, exit_code, stderr_str=getstderr(), stdout_str=getstdout(), stats=stats, started_at=begin)

    job_finished(FAILED, exit_code=exit_code, stderr_str=getstderr(), stdout_str=getstdout(), started_at=begin)



def run_rsync(dry_run: bool = True) -> dict:
    global rsync_process
    command = utils.create_rsync_command(dry_run)

    try:
        with open(report.get_temp_job_out_log_path(), "w") as stdout_log, \
            open(report.get_temp_job_err_log_path(), "w") as stderr_log:

            rsync_process = subprocess.Popen(
                command,
                stdout=stdout_log,
                stderr=stderr_log,
                text=True
            )
            logger.info(f"Starting rsync for {MIRRORR_JOB['name']}, rsync pid: {rsync_process.pid}")
            rsync_process.wait()
            return_code = rsync_process.returncode
            logger.info(f"Completed rsync run for {MIRRORR_JOB['name']} with exit code: {return_code}")

            return return_code, ""
    except Exception as e:
        exc_msg = f"{e}"
        logger.error(f"Error! {exc_msg}")
        return 1, exc_msg


def do_percentage_check(stats: dict, begin_time: float):
    if MIRRORR_JOB['rsync_delete'] is not True or MIRRORR_JOB['allowed_percentage'] == 100:
        logger.debug("Allowed percetange check skipped")
        return
    logger.debug("Running allowed percentage check")

    total_files_before = stats['total_files'] + stats['deleted']
    if total_files_before != 0:
        percentage_of_deleted = stats['deleted'] * 100 // total_files_before
        if percentage_of_deleted >= MIRRORR_JOB['allowed_percentage']:
            logger.debug(f"Allowed percentage exceeded ({stats['deleted']}, {percentage_of_deleted}% of total files), aborting job")
            message = f"Too many files would be deleted ({stats['deleted']} files, {percentage_of_deleted}%). Max allowed: {MIRRORR_JOB['allowed_percentage']}%"
            job_finished(ABORTED, 1, stderr_str=message, stats=stats, started_at=begin_time)


def job_finished(status:str, exit_code:int, started_at:int, stderr_str:str = "", stdout_str:str = "", stats: dict = {}):
    stats |= {'logfile_url': WEB_LOGS_URL + urllib.parse.quote(MIRRORR_JOB['name'])}

    duration = int(time.time() - started_at)
    stats |= {'duration': duration}
    stats |= {'human_readable_duration': utils.format_duration(duration)}
    stats |= {'human_readable_bytes_transferred': utils.format_bytes(stats.get('bytes_transferred', 0))}

    status_label = f'{status}{" -- DRY RUN" if MIRRORR_JOB["dryruns"] else ""}'
    logger.debug(f"Run completed for {MIRRORR_JOB['name']} with status label: {status_label}\nStats:\n{pprint.pformat(stats, indent=4)}")
    logger.debug("Updating logs and reporters...")

    if status == FAILED:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\nExit code: {exit_code}\n\n{stderr_str}")
        report.report(status_label, exit_code, message=stderr_str, stats=stats)
        sys.exit(1)
    elif status in [ABORTED, INVALID]:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nExit code: {exit_code}\n\n{stderr_str}")
        report.report(status_label, exit_code, message=stderr_str, stats=stats)
        sys.exit(1)
    elif status == KILLED:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\n{stderr_str}\nExit code: {exit_code}\n\n{stdout_str}")
        report.report(status_label, exit_code, message=stderr_str, stats=stats)
        sys.exit(0)
    elif status == UNKNOWN:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nExit code: {exit_code}\n\n{stdout_str}")
        report.report(status_label, exit_code, stats=stats, message="Unparseable rsync logs, job may have succeeded")
        sys.exit(0)
    elif status == NOOP:
        if MIRRORR_JOB['log_noop']:
            report.write_job_log(f"{status_label}\n\nNothing was transferred or deleted\n\nTook: {stats['human_readable_duration']}\nExit code: {exit_code}")
        if MIRRORR_JOB['report_noop']:
            report.report(status_label, exit_code, message="Nothing was transferred or deleted", stats=stats)
        sys.exit(0)
    elif status == SUCCESS:
        if MIRRORR_JOB['log_success']:
            report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\nExit code: {exit_code}\n\n{stdout_str}")
        if MIRRORR_JOB['report_success']:
            report.report(status_label, exit_code, message="All went well", stats=stats)
        sys.exit(0)
    elif status == PARTIAL_SUCCESS:
        report.write_job_log(f"{status_label}\n\nTook: {stats['human_readable_duration']}\nTransfered: {stats['human_readable_bytes_transferred']}\n{stderr_str}\nExit code: {exit_code}\n\n{stdout_str}")
        # Don't send whole stderr, the last line contains what happened
        summary = (lambda lines: lines[-1] if lines else "")(str(stderr_str).splitlines())
        report.report(status_label, exit_code, stats=stats, message=summary)
        sys.exit(0)

    sys.exit(1)


def create_mirrorr_conf(args):
    global MIRRORR_CONF
    global WEB_LOGS_URL
    logger.debug("Loading global config")

    mirrorr_conf = Path(args.datadir) / "conf.yaml"
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

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Loaded global config:\n{pprint.pformat(MIRRORR_CONF, indent=4)}")


def create_mirrorr_job(args):
    global MIRRORR_JOB

    datadir = Path(args.datadir)

    job_conf = datadir / f"jobs/{args.job}.yaml"
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


def setup_runtime(args):
    signal.signal(signal.SIGTERM, handle_termination)
    signal.signal(signal.SIGINT, handle_termination)

    report.DATA_DIR = args.datadir

    runtime_dir = Path(args.datadir) / ".runtime"
    if not runtime_dir.exists():
        runtime_dir.mkdir()


def handle_termination(signum, frame):
    global shutdown_triggered, rsync_process
    if shutdown_triggered:
        return
        
    logger.warning(f"Mirrorr received termination signal ({signal.Signals(signum).name}). Stopping current job...")
    shutdown_triggered = True

    if rsync_process and rsync_process.poll() is None:
        rsync_process.send_signal(signal.SIGINT) 



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the logging level")
    parser.add_argument('-datadir', help='Base data dir where all conf, jobs and logs are', required=True)
    parser.add_argument('-job', help='The name of the job to run', required=True)
    parser.add_argument('-fqdn_or_ip', help='Fully qualified domain name or IP of the mirrorr web server', required=True)
    parser.add_argument('-app_log_level', help='The application log level, unless job overrides this, mirrorr will use the app log level', required=True)
    args = parser.parse_args()

    setup_logging(args)
    logger.info("Mirrorr is starting the execution of a job")

    create_mirrorr_conf(args)
    logger.info("Conf loaded")

    setup_runtime(args)
    logger.info("Runtime ready")

    create_mirrorr_job(args)
    logger.info(f"Job loaded: {MIRRORR_JOB.get('name', 'error!')}")

    main()
