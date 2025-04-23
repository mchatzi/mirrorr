import argparse
import logging
import random
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from logging.handlers import RotatingFileHandler

from utils import *

logger = logging.getLogger(__package__)

app = Flask(__name__, static_folder='frontend')
CORS(app)


Path("data/jobs").mkdir(parents=True, exist_ok=True)
Path("data/logs").mkdir(parents=True, exist_ok=True)
Path("web/logs").mkdir(parents=True, exist_ok=True)

if not Path("data/conf.yaml").exists():
    save_settings({'color-theme': 'color-theme-green', 'o2reporter': { 'o2server-url': None, 'o2server-auth': None}})


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

# Direct access to job log files
@app.route('/data/logs/<path:path>')
def download_log(path):
    return send_file("../data/logs/" + path)  # TODO Fix this '..' (we are in /web)


@app.route('/css/theme.css')
def get_css_theme():
    color_theme = load_settings()['color-theme'] + ".css"
    return send_from_directory(app.static_folder, f"css/{color_theme}")


@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = load_jobs()
    for job in jobs:
        job['enabled'] = is_job_enabled(job)
        if job['enabled']:
            job['running'] = is_job_running(job)

    return jsonify(jobs)


@app.route('/api/jobs/<name>', methods=['GET'])
def get_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    job['enabled'] = is_job_enabled(job)
    if job['enabled']:
        job['running'] = is_job_running(job)

    return jsonify(job), 201


@app.route('/api/jobs', methods=['POST'])
def create_job():
    job = request.json

    validation_results = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))
    if validation_results:
        return jsonify({'validation': validation_results}), 400

    try:
        install_job(job)
        save_job(job)
    except Exception as e:
        return jsonify({'error': f"{e}"}), 500

    return jsonify(job), 201


@app.route('/api/jobs/<name>', methods=['PUT'])
def update_job(name):
    job = request.json
    
    if name != job['name']:
        return jsonify({'validation': 'Job name not equal to path param name'}), 400

    validation_results = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))
    if validation_results:
        return jsonify({'validation': validation_results}), 400

    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == name), None)
    if not existing_job:
        return jsonify({'error': 'Job not found'}), 404

    job_was_enabled = is_job_enabled(job)
    try:
        uninstall_job(job)
        install_job(job)
        if job_was_enabled:
            enable_job(job)
    except Exception as e:
        return jsonify({'error': f"{e}"}), 500

    save_job(job)

    return jsonify(job), 201


@app.route('/api/jobs/toggle', methods=['POST'])
def toggle_job():
    data = request.json
    enable = data['enable']
    name = data['name']

    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        if enable:
            enable_job(job)
        else:
            disable_job(job)
    except Exception as e:
        return jsonify({'error': f"{e}"}), 500

    return jsonify({'success': True})


@app.route('/api/jobs/<name>', methods=['DELETE'])
def delete_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        uninstall_job(job)
    except Exception as e:
        return jsonify({'error': f"{e}"}), 500

    delete_job_files(name)
    return jsonify({'deleted': True})


@app.route('/api/jobs/logs/<name>', methods=['GET'])
def get_job_logs(name):
    index = request.args.get("index", default=0, type=int)

    # We combine the requested log with all logs for this job
    response = {
        "all-logs": get_all_log_indices(name)
    }

    log = get_log(name, index)
    if log:
        response |= log
        return jsonify(response), 200
    else:
        return jsonify(response), 404


@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = load_settings();
    return jsonify(settings), 200


@app.route('/api/settings', methods=['POST'])
def set_settings():
    settings = request.json
    save_settings(settings)
    return jsonify({'success': True}), 200


def setup_logging():
    parser = argparse.ArgumentParser(description="Set the logging level via command line")
    parser.add_argument('--log', default='WARNING',
                        help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    args = parser.parse_args()
    logger.setLevel(args.log.upper())  # Set the logging level

    handler = RotatingFileHandler(
        "web/logs/mirrorr-web-be.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3)

    formatter = logging.Formatter(datefmt='%Y-%m-%d, %H:%M:%S',
                                  fmt='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return args.log.upper() == "DEBUG"


if __name__ == '__main__':
    is_debug = setup_logging()
    app.run(debug=is_debug, host='0.0.0.0', port=5000)
