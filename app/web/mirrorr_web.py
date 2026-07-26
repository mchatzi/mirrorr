import argparse
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory, send_file, render_template
from flask_cors import CORS
from utils import *
from mirrorr_be import *
from scheduler import start_scheduler

logger = logging.getLogger(__package__)

app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)


Path("data/jobs").mkdir(parents=True, exist_ok=True)
Path("data/logs").mkdir(parents=True, exist_ok=True)
Path("app/web/logs").mkdir(parents=True, exist_ok=True)

if not Path("data/conf.yaml").exists():
    save_settings({'color_theme': 'color-theme-green'})
else:
    settings = load_settings()
    if 'color_theme' not in settings:
        settings['color_theme'] = 'color-theme-green'
        save_settings(settings)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

# Direct access to job log files
@app.route('/data/logs/<path:path>', methods=['GET'])
def download_log(path):
    return send_file("../../data/logs/" + path)  # TODO Fix this '..' (we are in /app/web)


# Direct access to job conf files
@app.route('/data/jobs/<name>', methods=['GET'])
def export_job(name):
    return send_file(f"../../data/jobs/{name}.yaml")  # TODO Fix this '..' (we are in /app/web)


# Direct import to job conf file
@app.route('/data/jobs', methods=['POST'])
def import_job():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    job = yaml.safe_load(file)
    jobs = load_jobs()
    existing_job = next((j for j in jobs if j['name'] == job['name']), None)
    if existing_job:
        return 'A job with this name already exists', 400

    violations = validate_job(job, skip_path_existence_check=True)
    if violations:
       return ''.join(f"\n{key}: {value}" for v in violations for key, value in v.items()), 400

    try:
        save(job | {'enabled': False})
    except Exception as e:
        logger.error(e)
        return f"{e}", 500

    return 'OK'



# Direct access to mirrorr conf file
@app.route('/data/settings', methods=['GET'])
def export_mirrorr_conf():
    return send_file("../../data/conf.yaml")  # TODO Fix this '..' (we are in /web)


# Direct import to mirrorr conf file
@app.route('/data/settings', methods=['POST'])
def import_mirrorr_conf():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    #TODO Should do via be service
    file.save(str(Path("data/conf.yaml")))
    return 'OK'


@app.route('/css/theme.css')
def get_css_theme():
    color_theme = load_settings()['color_theme'] + ".css"
    return send_from_directory(app.static_folder, f"css/{color_theme}")


@app.route('/<path:path>')
def serve(path):
    if path.endswith('.html'):
        return render_template(path)
    return send_from_directory(app.static_folder, path)


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs= load_jobs()
    jobs.sort(key=lambda job: job.get("name", "").lower())

    #Decorate with execution info
    for job in jobs:
        job.update(get_job_execution(job['name']))

    return jsonify(jobs), 200


@app.route('/api/jobs/<name>', methods=['GET'])
def get_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

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
        save(job)
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

    if 'last_run' in existing_job: 
        job['last_run'] = existing_job['last_run']

    try:
        save(job)
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

    delete(name)
    return jsonify({'deleted': True}), 200


@app.route('/api/jobs/<name>/toggle', methods=['POST'])
def toggle_job(name):
    data = request.json
    do_enable = data['enable']

    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        if do_enable:
            enable(job)
        else:
            disable(job)
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


@app.route('/api/jobs/<name>/stop', methods=['GET'])
def stop_job(name):
    jobs = load_jobs()
    job = next((j for j in jobs if j['name'] == name), None)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        stop(name)
    except Exception as e:
        logger.error(e)
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

    #Decorate with version information
    settings['mirrorr_version'] = Path("install/.version").read_text().strip()
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
    
    log_level = args.log.upper()

    handler = RotatingFileHandler(
        "app/web/logs/mirrorr-web-be.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3)

    formatter = logging.Formatter(
        datefmt='%Y-%m-%d, %H:%M:%S',
        fmt='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
    )
    handler.setFormatter(formatter)

    # Add a StreamHandler so we can see errors directly in terminal/console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    root_logger.addHandler(console_handler)

    return log_level == "DEBUG"



if __name__ == '__main__':
    is_debug = setup_logging()
    start_scheduler()
    app.run(debug=is_debug, host='0.0.0.0', port=5000)
