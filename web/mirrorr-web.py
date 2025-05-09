import argparse
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from utils import *

logger = logging.getLogger(__package__)

app = Flask(__name__, static_folder='frontend')
CORS(app)


Path("data/jobs").mkdir(parents=True, exist_ok=True)
Path("data/logs").mkdir(parents=True, exist_ok=True)
Path("web/logs").mkdir(parents=True, exist_ok=True)

if not Path("data/conf.yaml").exists():
    save_settings({'color_theme': 'color-theme-green'})


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

# Direct access to job log files
@app.route('/data/logs/<path:path>', methods=['GET'])
def download_log(path):
    return send_file("../data/logs/" + path)  # TODO Fix this '..' (we are in /web)


# Direct access to job conf files
@app.route('/data/jobs/<name>', methods=['GET'])
def export_job(name):
    return send_file(f"../data/jobs/{name}.yaml")  # TODO Fix this '..' (we are in /web)


# Direct access to mirrorr conf file
@app.route('/data/settings/export', methods=['GET'])
def export_mirrorr_conf():
    return send_file("../data/conf.yaml")  # TODO Fix this '..' (we are in /web)


@app.route('/css/theme.css')
def get_css_theme():
    color_theme = load_settings()['color_theme'] + ".css"
    return send_from_directory(app.static_folder, f"css/{color_theme}")


@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = load_jobs()
    [job.update({'enabled': True}) for job in jobs if is_job_enabled(job)]
    [job.update({'running': True}) for job in jobs if job.get('enabled') and is_job_running(job)]

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

    violations = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))

    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == job['name']), None)
    if existing_job:
        violations.append({'name': 'A job with this name already exists'})

    if violations:
        return jsonify({'validation': violations}), 400

    try:
        install_job(job)
        save_job(job | {'dryruns': False})
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify(job), 201


@app.route('/api/jobs/<name>', methods=['PUT'])
def update_job(name):
    job = request.json

    if name != job['name']:
        return jsonify({'validation': 'Job name not equal to path param name'}), 400

    violations = validate_job(job, request.headers.get('Skip-Path-Existence-Check'))
    if violations:
        return jsonify({'validation': violations}), 400

    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == name), None)
    if not existing_job:
        return jsonify({'error': 'Job not found'}), 404

    job_was_enabled = is_job_enabled(job)
    job['dryruns'] = existing_job.get('dryruns') or False

    try:
        uninstall_job(job)
        install_job(job)
        if job_was_enabled:
            enable_job(job)
        save_job(job)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify(job), 201


@app.route('/api/jobs/<name>', methods=['DELETE'])
def delete_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        uninstall_job(job)
    except Exception as e:
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    delete_job_files(name)
    return jsonify({'deleted': True}), 200


@app.route('/api/jobs/<name>/toggle', methods=['POST'])
def toggle_job(name):
    data = request.json
    enable = data['enable']

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
        logger.error(e)
        return jsonify({'error': f"{e}"}), 500

    return jsonify({'success': True})


@app.route('/api/jobs/<name>/dryruns', methods=['POST'])
def toggle_dryruns(name):
    data = request.json
    enable = data['enable']

    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        if enable:
            enable_dryruns(job)
        else:
            disable_dryruns(job)
    except Exception as e:
        logger.error( f"{e}")
        return jsonify({'error': f"{e}"}), 500

    return jsonify({'success': True})


@app.route('/api/jobs/<name>/logs', methods=['GET'])
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


@app.route('/api/jobs/<name>/logs', methods=['DELETE'])
def delete_job_logs(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    purge_job_logs(name)
    return jsonify({'purged': True}), 200


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
